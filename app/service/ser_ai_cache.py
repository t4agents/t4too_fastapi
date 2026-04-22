from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from app.db.models.ai.ai_cache import AICacheDB
from app.service.ser_ai_context import AIContext


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _normalize_key(key: str) -> str:
    if len(key) <= 200:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"{key[:80]}:{digest}"


async def persistent_cache_get(ctx: AIContext, cache_key: str) -> Any | None:
    key = _normalize_key(cache_key)
    stmt = select(AICacheDB.value_json, AICacheDB.expires_at).where(
        AICacheDB.ten_id == ctx.ten_id,
        AICacheDB.cache_key == key,
        AICacheDB.cli_id == ctx.cli_id,
    )
    row = (await ctx.db.execute(stmt)).first()
    if not row:
        return None

    value, expires_at = row
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        await ctx.db.execute(
            delete(AICacheDB).where(
                AICacheDB.ten_id == ctx.ten_id,
                AICacheDB.cache_key == key,
                AICacheDB.cli_id == ctx.cli_id,
            )
        )
        return None
    return value


async def persistent_cache_set(
    ctx: AIContext,
    cache_key: str,
    value: Any,
    ttl_seconds: int | None = None,
) -> None:
    key = _normalize_key(cache_key)
    expires_at = None
    if ttl_seconds:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    payload = {
        "ten_id": ctx.ten_id,
        "biz_id": ctx.biz_id,
        "cli_id": ctx.cli_id,
        "usr_id": ctx.user_id,
        "created_by": ctx.user_id,
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
    await ctx.db.execute(stmt)
