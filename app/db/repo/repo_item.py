from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_tem import ItemDB
from app.db.repo.repo_utils import coerce_model_values


async def list_items(db: AsyncSession, zuid: UUID) -> List[ItemDB]:
    result = await db.execute(
        select(ItemDB)
        .where(ItemDB.created_by == zuid)
        .order_by(ItemDB.created_at.desc())
    )
    return list(result.scalars().all())

async def get_item_by_id(db: AsyncSession, item_id: UUID, zuid: UUID) -> Optional[ItemDB]:
    result = await db.execute(
        select(ItemDB).where(ItemDB.id == item_id, ItemDB.created_by == zuid)
    )
    return result.scalar_one_or_none()


async def create_item(db: AsyncSession, payload: dict) -> ItemDB:
    item = ItemDB(**coerce_model_values(ItemDB, payload))
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def update_item_fields(db: AsyncSession, item: ItemDB, updates: dict) -> ItemDB:
    if updates:
        for key, value in coerce_model_values(item, updates).items():
            setattr(item, key, value)
        db.add(item)
        await db.commit()
        await db.refresh(item)
    return item
