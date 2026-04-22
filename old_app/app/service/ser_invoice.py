from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.m_invoice import Invoice
from app.schemas.sch_invoice import InvoiceCreate


async def list_all_invoices(db: AsyncSession) -> List[Invoice]:
    """Get all invoices."""
    result = await db.execute(select(Invoice).order_by(Invoice.created_at.desc()))
    return list(result.scalars().all())


async def create_invoice(data: InvoiceCreate, db: AsyncSession) -> Invoice:
    """Create a new invoice."""
    invoice = Invoice(**data.model_dump())
    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)
    return invoice
