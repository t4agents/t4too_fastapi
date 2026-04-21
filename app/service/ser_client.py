from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_client import ZClientDB
from app.db.repo.repo_client import create_client as repo_create_client
from app.db.repo.repo_client import get_client_by_id, list_clients, update_client_fields


async def fetch_clients(zjwt: dict, db: AsyncSession) -> list[ZClientDB]:
    return await list_clients(db, zuid)


async def create_or_update_client(zjwt: dict, db: AsyncSession, payload: dict) -> ZClientDB:
    base_ids = {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }
    client_id = payload.get("id")
    if client_id:
        existing = await get_client_by_id(db, client_id, zuid)
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_client_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_client(db, data)
