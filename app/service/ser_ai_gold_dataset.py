from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select

from app.db.models.ai.ai_gold_dataset import RAGEvalDatasetDB
from app.schemas.sch_ai_gold_dataset import (
    GoldDatasetCreateRequest,
    GoldDatasetUpdateRequest,
)


async def list_gold_dataset(limit: int, db) -> list[RAGEvalDatasetDB]:
    stmt = (
        select(RAGEvalDatasetDB)
        .order_by(RAGEvalDatasetDB.id.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def create_gold_dataset(payload: GoldDatasetCreateRequest, db) -> RAGEvalDatasetDB:
    row = RAGEvalDatasetDB(
        question=payload.question,
        expected_answer=payload.expected_answer,
        relevant_source_ids=payload.relevant_source_ids,
        category=payload.category,
        difficulty=payload.difficulty,
        is_active=payload.is_active,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def update_gold_dataset(payload: GoldDatasetUpdateRequest, db) -> RAGEvalDatasetDB:
    try:
        row_id = UUID(payload.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid dataset id") from exc

    row = (
        await db.execute(select(RAGEvalDatasetDB).where(RAGEvalDatasetDB.id == row_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Dataset row not found")

    updates = payload.model_dump(exclude_unset=True)
    updates.pop("id", None)
    for key, value in updates.items():
        setattr(row, key, value)

    await db.flush()
    await db.refresh(row)
    return row
