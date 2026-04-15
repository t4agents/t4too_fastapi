from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.too.z_be import ZBizEntityDB
from app.schemas.sch_be import BizEntityOut, BizEntityUpdate
from app.service.ser_be import fetch_be_profile, update_be_profile
from app.service.ser_seed import apply_seed_defaults

beRou = APIRouter(prefix="/settings")


def _to_out(be: ZBizEntityDB) -> BizEntityOut:
    return BizEntityOut(
        be_type=be.be_type,
        be_name=be.be_name,
        be_logo=be.be_logo,
        be_contact=be.be_contact,
        be_contact_title=be.be_contact_title,
        be_address=be.be_address,
        be_email=be.be_email,
        be_phone=be.be_phone,
        be_website=be.be_website,
        be_biz_number=be.be_biz_number,
        be_tax_id=be.be_tax_id,
        be_bank_info=be.be_bank_info,
        be_payment_term=be.be_payment_term,
        be_currency=be.be_currency,
        be_inv_template_id=be.be_inv_template_id,
        be_description=be.be_description,
        be_note=be.be_note,
        be_timezone=be.be_timezone,
        be_date_format=be.be_date_format,
        be_inv_prefix=be.be_inv_prefix,
        be_inv_integer=be.be_inv_integer,
        be_inv_integer_max=be.be_inv_integer_max,
        be_show_paid_stamp=be.be_show_paid_stamp,
        be_plan_name=be.be_plan_name,
        be_plan251_expired=be.be_plan251_expired,
        be_plan252_expired=be.be_plan252_expired,
        be_plan253_expired=be.be_plan253_expired,
        be_plan254_expired=be.be_plan254_expired,
        be_plan255_expired=be.be_plan255_expired,
        be_plan256_expired=be.be_plan256_expired,
        be_plan257_expired=be.be_plan257_expired,
        be_plan258_expired=be.be_plan258_expired,
        be_plan259_expired=be.be_plan259_expired,
        be_number=be.be_number,
    )


@beRou.get("/be", response_model=BizEntityOut)
async def get_be_profile(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    try:
        be = await fetch_be_profile(zuid, db)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
        await apply_seed_defaults(zuid, db, reset=False)
        be = await fetch_be_profile(zuid, db)
    return _to_out(be)


@beRou.post("/be", response_model=BizEntityOut)
async def post_be_profile(
    payload: BizEntityUpdate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    updates = payload.model_dump(exclude_unset=True)
    try:
        be = await update_be_profile(zuid, db, updates)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
        await apply_seed_defaults(zuid, db, reset=False)
        be = await update_be_profile(zuid, db, updates)
    return _to_out(be)
