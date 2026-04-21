from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_payment_method import PaymentMethodDB
from app.db.repo.repo_utils import coerce_model_values


async def list_payment_methods(db: AsyncSession) -> List[PaymentMethodDB]:
    result = await db.execute(
        select(PaymentMethodDB)
        .order_by(PaymentMethodDB.created_at.desc())
    )
    return list(result.scalars().all())

async def get_payment_method_by_id(
    db: AsyncSession, method_id: UUID, zjwt: dict
) -> Optional[PaymentMethodDB]:
    result = await db.execute(
        select(PaymentMethodDB).where(PaymentMethodDB.id == method_id)
    )
    return result.scalar_one_or_none()


async def create_payment_method(db: AsyncSession, payload: dict) -> PaymentMethodDB:
    method = PaymentMethodDB(**coerce_model_values(PaymentMethodDB, payload))
    db.add(method)
    await db.commit()
    await db.refresh(method)
    return method


async def update_payment_method_fields(
    db: AsyncSession, method: PaymentMethodDB, updates: dict
) -> PaymentMethodDB:
    if updates:
        for key, value in coerce_model_values(method, updates).items():
            setattr(method, key, value)
        db.add(method)
        await db.commit()
        await db.refresh(method)
    return method
