from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class AIContext:
    ten_id: UUID | None
    biz_id: UUID | None
    cli_id: UUID
    user_id: UUID | None
    db: AsyncSession


def _to_uuid_or_none(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def ai_context_from_zjwt(zjwt: dict[str, Any], db: AsyncSession) -> AIContext:
    cli_id = UUID(str(zjwt["user_metadata"]["sbu_client_id"]))
    ten_id = _to_uuid_or_none((zjwt.get("app_metadata") or {}).get("sba_ten_id")) or cli_id
    user_id = _to_uuid_or_none(zjwt.get("zuid"))
    return AIContext(
        ten_id=ten_id,
        biz_id=cli_id,
        cli_id=cli_id,
        user_id=user_id,
        db=db,
    )
