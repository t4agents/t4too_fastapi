from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ainvoaic.i_nvoice import InvoiceDB


async def list_invoices(db: AsyncSession, zuid: UUID) -> List[InvoiceDB]:
    result = await db.execute(
        select(InvoiceDB)
        .where(InvoiceDB.created_by == zuid)
        .order_by(InvoiceDB.created_at.desc())
    )
    return list(result.scalars().all())


async def get_invoice_by_id(
    db: AsyncSession, inv_id: UUID, zuid: UUID
) -> Optional[InvoiceDB]:
    result = await db.execute(
        select(InvoiceDB).where(InvoiceDB.id == inv_id, InvoiceDB.created_by == zuid)
    )
    return result.scalar_one_or_none()


async def create_invoice(db: AsyncSession, payload: dict) -> InvoiceDB:
    inv = InvoiceDB(**payload)
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return inv


async def update_invoice_fields(
    db: AsyncSession, inv: InvoiceDB, updates: dict
) -> InvoiceDB:
    if updates:
        for key, value in updates.items():
            setattr(inv, key, value)
        db.add(inv)
        await db.commit()
        await db.refresh(inv)
    return inv
