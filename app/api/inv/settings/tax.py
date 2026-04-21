from uuid import UUID
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_jwks_decoded, get_zjwt
from app.db.conn.db_async import get_db_rls
from app.db.conn.db_rls import get_db_rls
from app.db.models.inv.i_tax import TaxDB
from app.schemas.sch_tax import TaxCreate, TaxOut
from app.service.ser_tax import create_or_update_tax, fetch_taxes

taxRou = APIRouter()
_log = logging.getLogger("app.http")


def _to_out(tax: TaxDB) -> TaxOut:
    return TaxOut(
        id=tax.id,
        tax_name=tax.tax_name,
        tax_rate=tax.tax_rate,
        tax_type=tax.tax_type,
        tax_note=tax.tax_note,
    )


@taxRou.get("/get_tax_list", response_model=list[TaxOut])
async def get_taxes(
    decoded: dict = Depends(get_jwks_decoded),
    zjwt: dict = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    taxes = await fetch_taxes(zjwt, db)
    return [_to_out(tax) for tax in taxes]


@taxRou.post("/post_tax", response_model=TaxOut)
async def post_tax(
    payload: TaxCreate,
    zjwt: dict = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    tax = await create_or_update_tax(zjwt, db, payload.model_dump(exclude_unset=True))
    return _to_out(tax)
