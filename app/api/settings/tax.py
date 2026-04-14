from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.ainvoaic.i_tax import TaxDB
from app.schemas.sch_tax import TaxCreate, TaxOut
from app.service.ser_tax import create_or_update_tax, fetch_taxes

taxRou = APIRouter(prefix="/settings")


def _to_out(tax: TaxDB) -> TaxOut:
    return TaxOut(
        id=tax.id,
        tax_name=tax.tax_name,
        tax_rate=tax.tax_rate,
        tax_type=tax.tax_type,
        tax_note=tax.tax_note,
    )


@taxRou.get("/itax", response_model=list[TaxOut])
async def get_taxes(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    taxes = await fetch_taxes(zuid, db)
    return [_to_out(tax) for tax in taxes]


@taxRou.post("/itax", response_model=TaxOut)
async def post_tax(
    payload: TaxCreate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    tax = await create_or_update_tax(zuid, db, payload.model_dump(exclude_unset=True))
    return _to_out(tax)
