from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_tax import TaxDB
from app.db.repo.repo_utils import coerce_model_values

_log = logging.getLogger("app.http")


async def list_taxes(db: AsyncSession, zjwt: JWType) -> List[TaxDB]:
    result = await db.execute(
        select(TaxDB).order_by(TaxDB.created_at.desc())
    )
    rows = list(result.scalars().all())
    _log.info("list_taxes result_count=%s zuid=%s", len(rows), zjwt["zuid"])
    return rows

async def get_tax_by_id(db: AsyncSession, tax_id: UUID, zjwt: JWType) -> Optional[TaxDB]:
    result = await db.execute(
        select(TaxDB).where(TaxDB.id == tax_id, TaxDB.created_by == zjwt["zuid"])
    )
    return result.scalar_one_or_none()


async def create_tax(db: AsyncSession, payload: dict) -> TaxDB:
    tax = TaxDB(**coerce_model_values(TaxDB, payload))
    db.add(tax)
    await db.commit()
    # # await db.refresh(tax)
    return tax


async def update_tax_fields(db: AsyncSession, tax: TaxDB, updates: dict) -> TaxDB:
    if updates:
        for key, value in coerce_model_values(tax, updates).items():
            setattr(tax, key, value)
        db.add(tax)
        await db.commit()
        # # await db.refresh(tax)
    return tax
