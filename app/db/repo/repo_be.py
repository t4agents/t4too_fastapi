from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_be import ZBizEntityDB
from app.db.repo.repo_utils import coerce_model_value, coerce_model_values


async def get_be_by_id(db: AsyncSession, be_id: UUID|None) -> Optional[ZBizEntityDB]:
    result = await db.execute(select(ZBizEntityDB).where(ZBizEntityDB.id == be_id))
    return result.scalar_one_or_none()


async def update_be_fields(db: AsyncSession, be: ZBizEntityDB, updates: dict) -> ZBizEntityDB:
    if updates:
        for key, value in coerce_model_values(be, updates).items():
            setattr(be, key, value)
        db.add(be)
        await db.commit()
        # await db.refresh(be)
    return be
