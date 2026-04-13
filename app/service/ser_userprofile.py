from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings_singleton
from app.db.models.too.z_user import ZUserDB
from app.db.repo.repo_userprofile import get_user_by_id, update_user_fields

_log = logging.getLogger(__name__)


async def fetch_user_profile(zuid: UUID, db: AsyncSession) -> ZUserDB:
    _log.info("userprofile fetch start sub=%s", zuid)
    user = await get_user_by_id(db, zuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found.",
        )
    return user


async def _update_supabase_user_meta(zuid: UUID, updates: dict[str, Any]) -> None:
    meta_updates = {}
    if "display_name" in updates:
        meta_updates["display_name"] = updates["display_name"]
    if "avatar" in updates:
        meta_updates["avatar"] = updates["avatar"]
    if not meta_updates:
        return

    settings = get_settings_singleton()
    service_key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    print("------------service_key", service_key[:8])
    if not service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase service role key missing.",
        )

    admin_url = f"{settings.JWKS_ISS.rstrip('/')}/admin/users/{zuid}"
    headers = {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }
    payload = {"user_metadata": meta_updates}

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.put(admin_url, json=payload, headers=headers)
        if resp.status_code >= 300:
            _log.error("supabase auth meta update failed status=%s body=%s",
                       resp.status_code, resp.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Supabase auth metadata update failed.",
            )


async def update_user_profile(zuid: UUID, db: AsyncSession, updates: dict) -> ZUserDB:
    user = await fetch_user_profile(zuid, db)
    user = await update_user_fields(db, user, updates)
    await _update_supabase_user_meta(zuid, updates)
    return user
