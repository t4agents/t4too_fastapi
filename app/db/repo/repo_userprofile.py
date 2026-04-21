from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_user import ZUserDB
from app.db.repo.repo_utils import coerce_model_values

_log = logging.getLogger(__name__)
    
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[ZUserDB]:
    result = await db.execute(select(ZUserDB).where(ZUserDB.id == user_id))
    return result.scalar_one_or_none()


async def update_user_fields(db: AsyncSession, user: ZUserDB, updates: dict) -> ZUserDB:
    _log.error("----------------failed", updates)
    _log.error("----------------aa")
    if updates:
        for key, value in coerce_model_values(user, updates).items():
            setattr(user, key, value)
        db.add(user)
        await db.commit()
        # await db.refresh(user)
    return user
