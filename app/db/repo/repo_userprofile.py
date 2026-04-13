from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_user import ZUserDB


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[ZUserDB]:
    result = await db.execute(select(ZUserDB).where(ZUserDB.id == user_id))
    return result.scalar_one_or_none()


async def update_user_fields(db: AsyncSession, user: ZUserDB, updates: dict) -> ZUserDB:
    if updates:
        for key, value in updates.items():
            setattr(user, key, value)
        async with db.begin():
            db.add(user)
    return user
