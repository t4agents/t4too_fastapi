from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ainvoaic.i_tem import ItemDB
from app.db.repo.repo_item import create_item as repo_create_item
from app.db.repo.repo_item import get_item_by_id, list_items, update_item_fields


async def fetch_items(zuid: UUID, db: AsyncSession) -> list[ItemDB]:
    return await list_items(db, zuid)


async def create_or_update_item(zuid: UUID, db: AsyncSession, payload: dict) -> ItemDB:
    base_ids = {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }
    item_id = payload.get("id")
    if item_id:
        existing = await get_item_by_id(db, item_id, zuid)
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_item_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_item(db, data)
