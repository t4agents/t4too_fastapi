from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_tem import ItemDB
from app.db.repo.repo_item import create_item as repo_create_item
from app.db.repo.repo_item import get_item_by_id, list_items, update_item_fields


async def fetch_items(zjwt: dict, db: AsyncSession) -> list[ItemDB]:
    return await list_items(db, zjwt)


async def create_or_update_item(zjwt: dict, db: AsyncSession, payload: dict) -> ItemDB:
    base_ids = {
        "ten_id": zjwt["app_metadata"]["sba_ten_id"],
        "biz_id": zjwt["zuid"],
        "usr_id": zjwt["zuid"],
        "cli_id": zjwt["user_metadata"]["sbu_client_id"],
        "created_by": zjwt["zuid"],
    }
    item_id = payload.get("id")
    if item_id:
        existing = await get_item_by_id(db, item_id, zjwt["zuid"])
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_item_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_item(db, data)
