from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import COADB, JeDraft, JeDraftLine, TransactionRaw
from app.schemas.sch_acc import DraftGenerateIn, DraftOut, DraftPatch
from app.services.ai_drafting import generate_je_draft

router = APIRouter(prefix="/je-drafts", tags=["je-drafts"])


def _draft_out(db: Session, draft: JeDraft) -> DraftOut:
    lines = list(db.execute(select(JeDraftLine).where(JeDraftLine.draft_id == draft.id)).scalars().all())
    return DraftOut(
        id=draft.id,
        transaction_id=draft.transaction_id,
        ai_model=draft.ai_model,
        confidence=draft.confidence,
        rationale=draft.rationale,
        memo=draft.memo,
        approved=draft.approved,
        suggested_at=draft.suggested_at,
        reviewed_at=draft.reviewed_at,
        lines=lines,
    )


@router.post("/generate", response_model=DraftOut)
def generate_draft(
    payload: DraftGenerateIn,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> DraftOut:
    txn = db.execute(
        select(TransactionRaw).where(and_(TransactionRaw.id == payload.transaction_id, TransactionRaw.owner_id == user.owner_id))
    ).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    accounts = list(db.execute(select(Account).where(Account.owner_id == user.owner_id, Account.is_active.is_(True))).scalars().all())
    if not accounts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts available. Create accounts first.")

    ai_payload = generate_je_draft(
        amount=txn.amount,
        description=txn.description,
        accounts=[{"code": a.code, "name": a.name, "type": a.type} for a in accounts],
    )
    confidence = Decimal(str(ai_payload.get("confidence", 0.5)))
    draft = JeDraft(
        owner_id=user.owner_id,
        transaction_id=txn.id,
        ai_model=settings.openai_model_default,
        confidence=confidence,
        rationale=str(ai_payload.get("rationale", "")),
        memo=str(ai_payload.get("memo", txn.description[:120])),
    )
    db.add(draft)
    db.flush()

    account_by_code = {a.code: a for a in accounts}
    lines_in = ai_payload.get("lines", [])
    for item in lines_in:
        account_code = str(item.get("account_code", "")).strip()
        account = account_by_code.get(account_code)
        if not account:
            continue
        amount = Decimal(str(item.get("amount", "0")))
        if amount <= 0:
            continue
        line_type = str(item.get("line_type", "")).lower()
        if line_type not in {"debit", "credit"}:
            continue
        db.add(
            JeDraftLine(
                draft_id=draft.id,
                account_id=account.id,
                line_type=line_type,
                amount=amount,
                note=item.get("note"),
            )
        )

    txn.status = "mapped"
    db.commit()
    db.refresh(draft)
    return _draft_out(db, draft)


@router.get("", response_model=list[DraftOut])
def list_drafts(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> list[DraftOut]:
    drafts = list(
        db.execute(select(JeDraft).where(JeDraft.owner_id == user.owner_id).order_by(JeDraft.suggested_at.desc())).scalars().all()
    )
    return [_draft_out(db, d) for d in drafts]


@router.get("/{draft_id}", response_model=DraftOut)
def get_draft(
    draft_id: UUID,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> DraftOut:
    draft = db.execute(select(JeDraft).where(and_(JeDraft.id == draft_id, JeDraft.owner_id == user.owner_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return _draft_out(db, draft)


@router.patch("/{draft_id}", response_model=DraftOut)
def patch_draft(
    draft_id: UUID,
    payload: DraftPatch,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> DraftOut:
    draft = db.execute(select(JeDraft).where(and_(JeDraft.id == draft_id, JeDraft.owner_id == user.owner_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if payload.memo is not None:
        draft.memo = payload.memo
    if payload.approved is not None:
        draft.approved = payload.approved
        draft.reviewed_at = datetime.now(timezone.utc)
        draft.approved_by = user.user_id

    if payload.lines is not None:
        db.execute(JeDraftLine.__table__.delete().where(JeDraftLine.draft_id == draft.id))
        for item in payload.lines:
            db.add(
                JeDraftLine(
                    draft_id=draft.id,
                    account_id=item.account_id,
                    line_type=item.line_type,
                    amount=item.amount,
                    note=item.note,
                )
            )

    db.commit()
    db.refresh(draft)
    return _draft_out(db, draft)

