from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_nvoice_payment import InvoicePaymentDB
from app.db.repo.repo_utils import coerce_model_values


async def list_invoice_payments(db: AsyncSession, inv_id: UUID) -> List[InvoicePaymentDB]:
    result = await db.execute(
        select(InvoicePaymentDB)
        .where(InvoicePaymentDB.inv_id == inv_id)
        .order_by(InvoicePaymentDB.created_at.desc())
    )
    return list(result.scalars().all())


async def get_invoice_payment_by_id(
    db: AsyncSession, payment_id: UUID, zjwt: dict
) -> Optional[InvoicePaymentDB]:
    result = await db.execute(
        select(InvoicePaymentDB).where(InvoicePaymentDB.id == payment_id)
    )
    return result.scalar_one_or_none()


async def create_invoice_payment(db: AsyncSession, payload: dict) -> InvoicePaymentDB:
    payment = InvoicePaymentDB(**coerce_model_values(InvoicePaymentDB, payload))
    db.add(payment)
    await db.flush()
    return payment


async def update_invoice_payment_fields(
    db: AsyncSession, payment: InvoicePaymentDB, updates: dict
) -> InvoicePaymentDB:
    if updates:
        for key, value in coerce_model_values(payment, updates).items():
            setattr(payment, key, value)
        db.add(payment)
        await db.flush()
    return payment


async def delete_invoice_payment(db: AsyncSession, payment: InvoicePaymentDB) -> None:
    await db.delete(payment)
    await db.flush()
