from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import JeDraft, JeDraftLine, JournalEntry, JournalEntryLine, TransactionRaw
from app.schemas.sch_acc import JournalEntryOut
from app.services.accounting import assert_draft_balanced, is_period_closed, yyyymm_from_date

router = APIRouter(prefix="/journal-entries", tags=["journal-entries"])


def _entry_out(db: Session, entry: JournalEntry) -> JournalEntryOut:
    lines = list(db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry.id)).scalars().all())
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
def post_from_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> JournalEntryOut:
    draft = db.execute(select(JeDraft).where(and_(JeDraft.id == draft_id, JeDraft.owner_id == user.owner_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    lines = list(db.execute(select(JeDraftLine).where(JeDraftLine.draft_id == draft.id)).scalars().all())
    if not lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Draft has no lines")

    try:
        assert_draft_balanced(lines)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    txn = None
    if draft.transaction_id:
        txn = db.execute(
            select(TransactionRaw).where(and_(TransactionRaw.id == draft.transaction_id, TransactionRaw.owner_id == user.owner_id))
        ).scalar_one_or_none()
    entry_date = txn.txn_date if txn else datetime.now(timezone.utc).date()
    period = yyyymm_from_date(entry_date)
    if is_period_closed(db, user.owner_id, period):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period is closed")

    je = JournalEntry(
        owner_id=user.owner_id,
        entry_date=entry_date,
        memo=draft.memo,
        source="ai",
        source_ref_id=draft.id,
        posted_by=user.user_id,
        period_yyyymm=period,
    )
    db.add(je)
    db.flush()
    for line in lines:
        db.add(
            JournalEntryLine(
                journal_entry_id=je.id,
                account_id=line.account_id,
                line_type=line.line_type,
                amount=line.amount,
                description=line.note,
            )
        )
    draft.approved = True
    draft.approved_by = user.user_id
    draft.reviewed_at = datetime.now(timezone.utc)
    if txn:
        txn.status = "posted"
    db.commit()
    db.refresh(je)
    return _entry_out(db, je)


@router.get("", response_model=list[JournalEntryOut])
def list_entries(
    period_yyyymm: int | None = None,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> list[JournalEntryOut]:
    stmt = select(JournalEntry).where(JournalEntry.owner_id == user.owner_id).order_by(JournalEntry.posted_at.desc())
    if period_yyyymm is not None:
        stmt = stmt.where(JournalEntry.period_yyyymm == period_yyyymm)
    entries = list(db.execute(stmt.limit(limit)).scalars().all())
    return [_entry_out(db, e) for e in entries]


@router.get("/{journal_entry_id}", response_model=JournalEntryOut)
def get_entry(
    journal_entry_id: UUID,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> JournalEntryOut:
    entry = db.execute(
        select(JournalEntry).where(and_(JournalEntry.id == journal_entry_id, JournalEntry.owner_id == user.owner_id))
    ).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return _entry_out(db, entry)


@router.post("/{journal_entry_id}/reverse", response_model=JournalEntryOut)
def reverse_entry(
    journal_entry_id: UUID,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> JournalEntryOut:
    original = db.execute(
        select(JournalEntry).where(and_(JournalEntry.id == journal_entry_id, JournalEntry.owner_id == user.owner_id))
    ).scalar_one_or_none()
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    original_lines = list(db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == original.id)).scalars().all())
    if not original_lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Journal entry has no lines")

    period = yyyymm_from_date(datetime.now(timezone.utc).date())
    if is_period_closed(db, user.owner_id, period):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Current period is closed")

    reversal = JournalEntry(
        owner_id=user.owner_id,
        entry_date=datetime.now(timezone.utc).date(),
        memo=f"Reversal of entry {original.entry_no}",
        source="reversal",
        source_ref_id=original.id,
        posted_by=user.user_id,
        period_yyyymm=period,
        is_reversal=True,
        reversed_entry_id=original.id,
    )
    db.add(reversal)
    db.flush()
    for line in original_lines:
        db.add(
            JournalEntryLine(
                journal_entry_id=reversal.id,
                account_id=line.account_id,
                line_type="credit" if line.line_type == "debit" else "debit",
                amount=Decimal(line.amount),
                description=f"Reversal: {line.description or ''}".strip(),
            )
        )
    db.commit()
    db.refresh(reversal)
    return _entry_out(db, reversal)

