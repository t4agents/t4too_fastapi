from datetime import datetime, timezone
from decimal import Decimal
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings_singleton
from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import COADB, JeDraftDB, JeDraftLineDB, TransactionRawDB
from app.schemas.sch_acc import DraftGenerateIn, DraftLineOut, DraftOut, DraftPatch, LineType
from app.schemas.sch_ai import JWType
from app.service.acc.ai_drafting import generate_je_draft

router = APIRouter(prefix="/je-drafts", tags=["je-drafts"])
settings = get_settings_singleton()
OPENAI_MODEL_DEFAULT = getattr(settings, "OPENAI_MODEL_DEFAULT", "gpt-5-mini")
_LINE_TYPES: set[str] = {"debit", "credit"}


async def _draft_out(db: AsyncSession, draft: JeDraftDB) -> DraftOut:
    line_rows = list((await db.execute(select(JeDraftLineDB).where(JeDraftLineDB.draft_id == draft.id))).scalars().all())
    lines = [
        DraftLineOut(
            id=line.id,
            draft_id=line.draft_id,
            account_id=line.account_id,
            line_type=cast(LineType, line.line_type if line.line_type in _LINE_TYPES else "debit"),
            amount=line.amount,
            note=line.note,
        )
        for line in line_rows
    ]
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
async def generate_draft(
    payload: DraftGenerateIn,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> DraftOut:
    txn = (await db.execute(select(TransactionRawDB).where(TransactionRawDB.id == payload.transaction_id))).scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    accounts = list((await db.execute(select(COADB).where(COADB.is_deleted.is_not(True)))).scalars().all())
    if not accounts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No accounts available. Create accounts first.")

    ai_payload = generate_je_draft(
        amount=txn.amount,
        description=txn.description,
        accounts=[{"code": a.code, "name": a.name, "type": a.type} for a in accounts],
    )
    draft = JeDraftDB(
        ten_id=zjwt.ztid,
        biz_id=zjwt.zbid,
        cli_id=zjwt.zcid,
        usr_id=zjwt.zuid,
        created_by=zjwt.zuid,
        transaction_id=txn.id,
        ai_model=OPENAI_MODEL_DEFAULT,
        confidence=Decimal(str(ai_payload.get("confidence", 0.5))),
        rationale=str(ai_payload.get("rationale", "")),
        memo=str(ai_payload.get("memo", txn.description[:120])),
    )
    db.add(draft)
    await db.flush()

    account_by_code = {a.code: a for a in accounts}
    for item in ai_payload.get("lines", []):
        account = account_by_code.get(str(item.get("account_code", "")).strip())
        if not account:
            continue
        amount = Decimal(str(item.get("amount", "0")))
        line_type = str(item.get("line_type", "")).lower()
        if amount <= 0 or line_type not in {"debit", "credit"}:
            continue
        db.add(JeDraftLineDB(draft_id=draft.id, account_id=account.id, line_type=line_type, amount=amount, note=item.get("note")))

    txn.status = "mapped"
    await db.commit()
    await db.refresh(draft)
    return await _draft_out(db, draft)


@router.get("", response_model=list[DraftOut])
async def list_drafts(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> list[DraftOut]:
    drafts = list((await db.execute(select(JeDraftDB).order_by(JeDraftDB.suggested_at.desc()))).scalars().all())
    return [await _draft_out(db, d) for d in drafts]


@router.get("/{draft_id}", response_model=DraftOut)
async def get_draft(
    draft_id: UUID,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> DraftOut:
    draft = (await db.execute(select(JeDraftDB).where(JeDraftDB.id == draft_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return await _draft_out(db, draft)


@router.patch("/{draft_id}", response_model=DraftOut)
async def patch_draft(
    draft_id: UUID,
    payload: DraftPatch,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> DraftOut:
    draft = (await db.execute(select(JeDraftDB).where(JeDraftDB.id == draft_id))).scalar_one_or_none()
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")

    if payload.memo is not None:
        draft.memo = payload.memo
    if payload.approved is not None:
        draft.approved = payload.approved
        draft.reviewed_at = datetime.now(timezone.utc)
        draft.approved_by = zjwt.zuid
    if payload.lines is not None:
        await db.execute(delete(JeDraftLineDB).where(JeDraftLineDB.draft_id == draft.id))
        for item in payload.lines:
            db.add(JeDraftLineDB(draft_id=draft.id, account_id=item.account_id, line_type=item.line_type, amount=item.amount, note=item.note))

    await db.commit()
    await db.refresh(draft)
    return await _draft_out(db, draft)
