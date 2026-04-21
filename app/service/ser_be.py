from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_be import ZBizEntityDB
from app.db.repo.repo_be import get_be_by_id, update_be_fields

_log = logging.getLogger(__name__)


async def fetch_be_profile(zjwt: dict, db: AsyncSession) -> ZBizEntityDB:
    _log.info("be fetch start sub=%s", zuid)
    be = await get_be_by_id(db, zuid)
    if not be:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business entity not found.",
        )
    return be


async def update_be_profile(zjwt: dict, db: AsyncSession, updates: dict) -> ZBizEntityDB:
    be = await fetch_be_profile(zjwt["zuid"], db)
    be = await update_be_fields(db, be, updates)
    return be
