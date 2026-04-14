from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ainvoaic.i_fee import FeeDB


async def list_fees(db: AsyncSession, zuid: UUID) -> List[FeeDB]:
    result = await db.execute(
        select(FeeDB)
        .where(FeeDB.created_by == zuid)
        .order_by(FeeDB.created_at.desc())
    )
    return list(result.scalars().all())

async def get_fee_by_id(db: AsyncSession, fee_id: UUID, zuid: UUID) -> Optional[FeeDB]:
    result = await db.execute(
        select(FeeDB).where(FeeDB.id == fee_id, FeeDB.created_by == zuid)
    )
    return result.scalar_one_or_none()


async def create_fee(db: AsyncSession, payload: dict) -> FeeDB:
    fee = FeeDB(**payload)
    db.add(fee)
    await db.commit()
    await db.refresh(fee)
    return fee


async def update_fee_fields(db: AsyncSession, fee: FeeDB, updates: dict) -> FeeDB:
    if updates:
        for key, value in updates.items():
            setattr(fee, key, value)
        db.add(fee)
        await db.commit()
        await db.refresh(fee)
    return fee
