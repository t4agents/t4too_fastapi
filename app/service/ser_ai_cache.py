from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sch_ai import JWType
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from app.db.models.ai.ai_cache import AICacheDB


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _normalize_key(key: str) -> str:
    if len(key) <= 200:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"{key[:80]}:{digest}"


async def persistent_cache_get(zjwt: JWType, cache_key: str, db: AsyncSession) -> Any | None:
    key = _normalize_key(cache_key)
    stmt = select(AICacheDB.value_json, AICacheDB.expires_at).where(
        AICacheDB.ten_id == zjwt.ztid,
        AICacheDB.cache_key == key,
        AICacheDB.cli_id == zjwt.zcid,
    )
    row = (await db.execute(stmt)).first()
    if not row:
        return None

    value, expires_at = row
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        await db.execute(
            delete(AICacheDB).where(
                AICacheDB.ten_id == zjwt.ztid,
                AICacheDB.cache_key == key,
                AICacheDB.cli_id == zjwt.zcid,
            )
        )
        return None
    return value


async def persistent_cache_set(
    zjwt: JWType,
    cache_key: str,
    value: Any,
    db: AsyncSession,
    ttl_seconds: int | None = None,
) -> None:
    key = _normalize_key(cache_key)
    expires_at = None
    if ttl_seconds:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    payload = {
        "ten_id": zjwt.ztid,
        "biz_id": zjwt.zbid,
        "cli_id": zjwt.zcid,
        "usr_id": zjwt.zuid,
        "created_by": zjwt.zuid,
        "cache_key": key,
        "value_json": _json_safe(value),
        "expires_at": expires_at,
        "updated_at": func.now(),
    }
    stmt = insert(AICacheDB).values(payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ten_id", "cache_key"],
        set_=payload,
    )
    await db.execute(stmt)
