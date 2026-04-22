import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_agent_cache import AgentCache


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _normalize_key(key: str) -> str:
    if len(key) <= 200:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"{key[:80]}:{digest}"


async def persistent_cache_get(zme: ZMeDataClass, cache_key: str) -> Any | None:
    key = _normalize_key(cache_key)
    stmt = select(AgentCache.value_json, AgentCache.expires_at).where(
        AgentCache.ten_id == zme.ztid,
        AgentCache.cache_key == key,
    )
    res = await zme.zdb.execute(stmt)
    row = res.first()
    if not row:
        return None
    value, expires_at = row
    if expires_at is not None and expires_at <= datetime.now(timezone.utc):
        await zme.zdb.execute(
            delete(AgentCache).where(
                AgentCache.ten_id == zme.ztid,
                AgentCache.cache_key == key,
            )
        )
        return None
    return value


async def persistent_cache_set(
    zme: ZMeDataClass,
    cache_key: str,
    value: Any,
    ttl_seconds: int | None = None,
) -> None:
    key = _normalize_key(cache_key)
    expires_at = None
    if ttl_seconds:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    payload = {
        "ten_id": zme.ztid,
        "biz_id": zme.zbid,
        "cache_key": key,
        "value_json": _json_safe(value),
        "expires_at": expires_at,
        "updated_at": func.now(),
    }
    stmt = insert(AgentCache).values(payload)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ten_id", "cache_key"],
        set_=payload,
    )
    await zme.zdb.execute(stmt)
