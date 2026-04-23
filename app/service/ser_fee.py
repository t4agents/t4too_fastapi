from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_fee import FeeDB
from app.db.repo.repo_fee import create_fee as repo_create_fee
from app.db.repo.repo_fee import get_fee_by_id, list_fees, update_fee_fields


async def fetch_fees(zjwt: JWType, db: AsyncSession) -> list[FeeDB]:
    return await list_fees(db, zjwt["zuid"])


async def create_or_update_fee(zjwt: JWType, db: AsyncSession, payload: dict) -> FeeDB:
    base_ids = {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }
    fee_id = payload.get("id")
    if fee_id:
        existing = await get_fee_by_id(db, fee_id, zjwt["zuid"])
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_fee_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_fee(db, data)
