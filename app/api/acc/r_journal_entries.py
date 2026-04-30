from datetime import datetime, timezone
from decimal import Decimal
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import JeDraftDB, JeDraftLineDB, JournalEntryDB, JournalEntryLine, TransactionRawDB
from app.schemas.sch_acc import JournalEntryOut, JournalLineOut, LineType
from app.schemas.sch_ai import JWType
from app.service.acc.accounting import assert_draft_balanced, is_period_closed, yyyymm_from_date

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])
_LINE_TYPES: set[str] = {"debit", "credit"}


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


@router.post("/from-draft/{draft_id}", response_model=JournalEntryOut, status_code=status.HTTP_201_CREATED)
async def post_from_draft(
    draft_id: UUID,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> JournalEntryOut:
    draft = (await db.execute(select(JeDraftDB).where(JeDraftDB.id == draft_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    lines = list((await db.execute(select(JeDraftLineDB).where(JeDraftLineDB.draft_id == draft.id))).scalars().all())
    if not lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft has no lines")
    assert_draft_balanced(lines)

    txn = None
    if draft.transaction_id:
        txn = (await db.execute(select(TransactionRawDB).where(TransactionRawDB.id == draft.transaction_id))).scalar_one_or_none()
    entry_date = txn.txn_date if txn else datetime.now(timezone.utc).date()
    period = yyyymm_from_date(entry_date)
    if await is_period_closed(db, period):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period is closed")

    je = JournalEntryDB(
        ten_id=zjwt.ztid,
        biz_id=zjwt.zbid,
        cli_id=zjwt.zcid,
        usr_id=zjwt.zuid,
        created_by=zjwt.zuid,
        entry_date=entry_date,
        memo=draft.memo,
        source="ai",
        source_ref_id=draft.id,
        posted_by=zjwt.zuid,
        period_yyyymm=period,
    )
    db.add(je)
    await db.flush()
    for line in lines:
        db.add(JournalEntryLine(journal_entry_id=je.id, account_id=line.account_id, line_type=line.line_type, amount=line.amount, description=line.note))

    draft.approved = True
    draft.approved_by = zjwt.zuid
    draft.reviewed_at = datetime.now(timezone.utc)
    if txn:
        txn.status = "posted"
    await db.commit()
    await db.refresh(je)
    return await _entry_out(db, je)


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
        cli_id=zjwt.zcid,
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
        db.add(JournalEntryLine(journal_entry_id=reversal.id, account_id=line.account_id, line_type="credit" if line.line_type == "debit" else "debit", amount=Decimal(line.amount), description=f"Reversal: {line.description or ''}".strip()))

    await db.commit()
    await db.refresh(reversal)
    return await _entry_out(db, reversal)
