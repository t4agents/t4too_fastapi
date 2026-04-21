from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_nvoice_item import InvoiceItemDB


async def list_invoice_items(db: AsyncSession, inv_id: UUID) -> List[InvoiceItemDB]:
    result = await db.execute(select(InvoiceItemDB)
        .where(InvoiceItemDB.inv_id == inv_id)
        .order_by(InvoiceItemDB.created_at.desc())
    )
    return list(result.scalars().all())
