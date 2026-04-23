from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_tax import TaxDB
from app.db.repo.repo_tax import create_tax as repo_create_tax
from app.db.repo.repo_tax import get_tax_by_id, list_taxes, update_tax_fields


async def fetch_taxes(zjwt: JWType, db: AsyncSession) -> list[TaxDB]:
    return await list_taxes(db, zjwt)


async def create_or_update_tax(zjwt: JWType, db: AsyncSession, payload: dict) -> TaxDB:
    base_ids = {
        "ten_id": zjwt["zuid"],
        "biz_id": zjwt["zuid"],
        "usr_id": zjwt["zuid"],
        "cli_id": zjwt["zuid"],
        "created_by": zjwt["zuid"],
    }
    tax_id = payload.get("id")
    if tax_id:
        existing = await get_tax_by_id(db, tax_id, zjwt)
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_tax_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_tax(db, data)
