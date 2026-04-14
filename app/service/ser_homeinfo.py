from __future__ import annotations

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_user import ZUserDB
from app.db.repo.repo_be import get_be_by_id
from app.db.repo.repo_userprofile import get_user_by_id

_log = logging.getLogger(__name__)


async def fetch_homeinfo(
    zuid: UUID,
    db: AsyncSession,
) -> tuple[ZUserDB, ZBizEntityDB | None]:
    _log.info("homeinfo fetch start sub=%s", zuid)
    user = await get_user_by_id(db, zuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Home info not found.",
        )
    be = await get_be_by_id(db, zuid)
    return user, be
