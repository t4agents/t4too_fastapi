from datetime import datetime, timezone
from decimal import Decimal
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import COADB, JournalEntryDB, JournalEntryLine, TransactionRawDB
from app.schemas.sch_acc import JournalEntryOut, JournalGenerateIn, JournalLineOut, LineType
from app.schemas.sch_ai import JWType
from app.service.acc.accounting import is_period_closed, yyyymm_from_date
from app.service.acc.ai_drafting import generate_je_draft

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])
_LINE_TYPES: set[str] = {"debit", "credit"}


async def create_ai_entry_for_transaction(
    txn: TransactionRawDB,
    zjwt: JWType,
    db: AsyncSession,
) -> JournalEntryOut:
    period = yyyymm_from_date(txn.txn_date)
    if await is_period_closed(db, period):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period is closed")

    accounts = list((await db.execute(select(COADB).where(COADB.is_deleted.is_not(True)))).scalars().all())
    if not accounts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts available. Create accounts first.")

    ai_payload = generate_je_draft(
        amount=txn.amount,
        description=txn.description,
        accounts=[{"code": a.code, "name": a.name, "type": a.type} for a in accounts],
    )

    account_by_code = {a.code: a for a in accounts}
    candidate_lines: list[tuple[UUID, str, Decimal, str | None]] = []
    for item in ai_payload.get("lines", []):
        account = account_by_code.get(str(item.get("account_code", "")).strip())
        if not account:
            continue
        amount = Decimal(str(item.get("amount", "0")))
        line_type = str(item.get("line_type", "")).lower()
        if amount <= 0 or line_type not in _LINE_TYPES:
            continue
        candidate_lines.append((account.id, line_type, amount, item.get("note")))

    if not candidate_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI did not produce valid journal lines")

    debit_total = sum((amount for _, line_type, amount, _ in candidate_lines if line_type == "debit"), Decimal("0"))
    credit_total = sum((amount for _, line_type, amount, _ in candidate_lines if line_type == "credit"), Decimal("0"))
    if debit_total != credit_total:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Generated journal lines are not balanced")

    je = JournalEntryDB(
        ten_id=zjwt.ztid,
        biz_id=zjwt.zbid,
        usr_id=zjwt.zuid,
        created_by=zjwt.zuid,
        entry_date=txn.txn_date,
        memo=str(ai_payload.get("memo", txn.description[:120])),
        source="ai",
        source_ref_id=txn.id,
        posted_by=zjwt.zuid,
        period_yyyymm=period,
    )
    db.add(je)
    await db.flush()
    for account_id, line_type, amount, note in candidate_lines:
        db.add(
            JournalEntryLine(
                journal_entry_id=je.id,
                account_id=account_id,
                line_type=line_type,
                amount=amount,
                description=note,
                ten_id=zjwt.ztid,
                biz_id=zjwt.zbid,
                usr_id=zjwt.zuid,
                created_by=zjwt.zuid,
            )
        )

    txn.status = "posted"
    await db.commit()
    await db.refresh(je)
    return await _entry_out(db, je)


@router.post("/generate", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
async def generate_entry(
    payload: JournalGenerateIn,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> JournalEntryOut:
    txn = (await db.execute(select(TransactionRawDB).where(TransactionRawDB.id == payload.transaction_id))).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return await create_ai_entry_for_transaction(txn=txn, zjwt=zjwt, db=db)


async def _entry_out(db: AsyncSession, entry: JournalEntryDB) -> JournalEntryOut:
    line_rows = list((await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry.id))).scalars().all())
    lines = [
        JournalLineOut(
            id=line.id,
            journal_entry_id=line.journal_entry_id,
            account_id=line.account_id,
            line_type=cast(LineType, line.line_type if line.line_type in _LINE_TYPES else "debit"),
            amount=line.amount,
            description=line.description,
        )
        for line in line_rows
    ]
    return JournalEntryOut(
        id=entry.id,
        entry_no=entry.entry_no,
        entry_date=entry.entry_date,
        memo=entry.memo,
        source=entry.source,
        period_yyyymm=entry.period_yyyymm,
        posted_at=entry.posted_at,
        is_reversal=entry.is_reversal,
        lines=lines,
    )


@router.get("", response_model=list[JournalEntryOut])
async def list_entries(
    period_yyyymm: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> list[JournalEntryOut]:
    stmt = select(JournalEntryDB).order_by(JournalEntryDB.posted_at.desc())
    if period_yyyymm is not None:
        stmt = stmt.where(JournalEntryDB.period_yyyymm == period_yyyymm)
    entries = list((await db.execute(stmt.limit(limit))).scalars().all())
    return [await _entry_out(db, e) for e in entries]


@router.get("/{journal_entry_id}", response_model=JournalEntryOut)
async def get_entry(
    journal_entry_id: UUID,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> JournalEntryOut:
    entry = (await db.execute(select(JournalEntryDB).where(JournalEntryDB.id == journal_entry_id))).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return await _entry_out(db, entry)


@router.post("/{journal_entry_id}/reverse", response_model=JournalEntryOut)
async def reverse_entry(
    journal_entry_id: UUID,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> JournalEntryOut:
    original = (await db.execute(select(JournalEntryDB).where(JournalEntryDB.id == journal_entry_id))).scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    original_lines = list((await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == original.id))).scalars().all())
    if not original_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Journal entry has no lines")

    period = yyyymm_from_date(datetime.now(timezone.utc).date())
    if await is_period_closed(db, period):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Current period is closed")

    reversal = JournalEntryDB(
        ten_id=zjwt.ztid,
        biz_id=zjwt.zbid,
        usr_id=zjwt.zuid,
        created_by=zjwt.zuid,
        entry_date=datetime.now(timezone.utc).date(),
        memo=f"Reversal of entry {original.entry_no}",
        source="reversal",
        source_ref_id=original.id,
        posted_by=zjwt.zuid,
        period_yyyymm=period,
        is_reversal=True,
        reversed_entry_id=original.id,
    )
    db.add(reversal)
    await db.flush()
    for line in original_lines:
        db.add(
            JournalEntryLine(
                journal_entry_id=reversal.id,
                account_id=line.account_id,
                line_type="credit" if line.line_type == "debit" else "debit",
                amount=Decimal(line.amount),
                description=f"Reversal: {line.description or ''}".strip(),
                ten_id=zjwt.ztid,
                biz_id=zjwt.zbid,
                usr_id=zjwt.zuid,
                created_by=zjwt.zuid,
            )
        )

    await db.commit()
    await db.refresh(reversal)
    return await _entry_out(db, reversal)
