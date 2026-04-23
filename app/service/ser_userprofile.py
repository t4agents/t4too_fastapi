from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_admin import get_supabase_admin_client
from app.db.models.too.z_user import ZUserDB
from app.db.repo.repo_userprofile import get_user_by_id, update_user_fields

_log = logging.getLogger(__name__)


async def fetch_user_profile(zjwt: JWType, db: AsyncSession) -> ZUserDB:
    user = await get_user_by_id(db, zjwt["zuid"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.",
        )
    return user


async def _update_supabase_user_meta(zjwt: JWType, updates: dict[str, Any]) -> None:
    zuid = zjwt["zuid"]
    meta_updates = {}
    if "display_name" in updates:
        meta_updates["display_name"] = updates["display_name"]
    if "avatar" in updates:
        meta_updates["sbu_avatar"] = updates["avatar"]
    if "sbu_avatar" in updates:
        meta_updates["sbu_avatar"] = updates["sbu_avatar"]
    if not meta_updates:
        return

    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(
            str(zuid),
            {"user_metadata": meta_updates},
        )
    except Exception as exc:
        _log.error("supabase auth meta update failed zuid=%s err=%s", zuid, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase auth metadata update failed.",
        ) from exc


async def update_user_profile(zjwt: JWType, db: AsyncSession, updates: dict) -> ZUserDB:
    user = await fetch_user_profile(zjwt, db)
    user = await update_user_fields(db, user, updates)
    await _update_supabase_user_meta(zjwt, updates)
    return user
