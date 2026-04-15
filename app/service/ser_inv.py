from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ainvoaic.i_nvoice import InvoiceDB
from app.db.repo.repo_inv import list_invoices


async def fetch_invoices(zuid: UUID, db: AsyncSession) -> list[InvoiceDB]:
    return await list_invoices(db, zuid)

