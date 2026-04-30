from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import TransactionRaw
from app.schemas.sch_acc import TransactionOut
from app.services.accounting import import_transactions, parse_csv_transactions

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")
    content = await file.read()
    txns = parse_csv_transactions(content, user.owner_id, file.filename, settings.default_currency)
    result = import_transactions(db, user.owner_id, txns)
    return {
        "imported_count": result.imported_count,
        "duplicate_count": result.duplicate_count,
        "transaction_ids": result.ids,
    }


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    status_filter: str | None = Query(default=None, alias="status"),
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> list[TransactionRaw]:
    stmt = select(TransactionRaw).where(TransactionRaw.owner_id == user.owner_id).order_by(TransactionRaw.txn_date.desc())
    if status_filter:
        stmt = stmt.where(TransactionRaw.status == status_filter)
    if from_date:
        stmt = stmt.where(TransactionRaw.txn_date >= from_date)
    if to_date:
        stmt = stmt.where(TransactionRaw.txn_date <= to_date)
    stmt = stmt.limit(max(1, min(500, limit)))
    return list(db.execute(stmt).scalars().all())


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> TransactionRaw:
    txn = db.execute(
        select(TransactionRaw).where(and_(TransactionRaw.id == transaction_id, TransactionRaw.owner_id == user.owner_id))
    ).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn

