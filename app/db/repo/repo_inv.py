from __future__ import annotations

from typing import List
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

