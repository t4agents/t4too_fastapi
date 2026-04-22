from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.db_async import get_session
from app.schemas.sch_invoice import InvoiceCreate, InvoiceResponse
from app.service.ser_invoice import list_all_invoices, create_invoice

invoiceRou = APIRouter()


@invoiceRou.get("", response_model=List[InvoiceResponse])
async def list_all(
    db: AsyncSession = Depends(get_session),
):
    """List all invoices."""
    return await list_all_invoices(db)


@invoiceRou.post("", response_model=InvoiceResponse)
async def generate_new(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new invoice for testing."""
    return await create_invoice(data, db)
