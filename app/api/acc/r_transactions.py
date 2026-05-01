from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings_singleton
from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import TransactionRawDB
from app.schemas.sch_acc import TransactionOut
from app.schemas.sch_ai import JWType
from app.service.acc.accounting import import_transactions, parse_csv_transactions
from .r_journal_entries import create_ai_entry_for_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])
settings = get_settings_singleton()
DEFAULT_CURRENCY = getattr(settings, "DEFAULT_CURRENCY", "CAD")


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")
    if not zjwt.ztid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tenant id in JWT")
    content = await file.read()
    txns = parse_csv_transactions(content, zjwt.ztid, file.filename, DEFAULT_CURRENCY)
    result = await import_transactions(db, txns)

    created_entry_ids: list[str] = []
    entry_failed_count = 0
    if result.ids:
        txn_ids = [UUID(txn_id) for txn_id in result.ids]
        imported_rows = list((await db.execute(select(TransactionRawDB).where(TransactionRawDB.id.in_(txn_ids)))).scalars().all())
        for txn in imported_rows:
            try:
                entry = await create_ai_entry_for_transaction(txn=txn, zjwt=zjwt, db=db)
                created_entry_ids.append(str(entry.id))
            except HTTPException:
                entry_failed_count += 1

    return {
        "imported_count": result.imported_count,
        "duplicate_count": result.duplicate_count,
        "transaction_ids": result.ids,
        "journal_entry_count": len(created_entry_ids),
        "journal_entry_ids": created_entry_ids,
        "journal_entry_failed_count": entry_failed_count,
    }


@router.get("", response_model=list[TransactionOut])
async def list_transactions(
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> list[TransactionRawDB]:
    stmt = select(TransactionRawDB).order_by(TransactionRawDB.txn_date.desc())
    if status_filter:
        stmt = stmt.where(TransactionRawDB.status == status_filter)
    if from_date:
        stmt = stmt.where(TransactionRawDB.txn_date >= from_date)
    if to_date:
        stmt = stmt.where(TransactionRawDB.txn_date <= to_date)
    stmt = stmt.limit(max(1, min(500, limit)))
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{transaction_id}", response_model=TransactionOut)
async def get_transaction(
    transaction_id: UUID,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> TransactionRawDB:
    txn = (await db.execute(select(TransactionRawDB).where(TransactionRawDB.id == transaction_id))).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn
