from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.conn.db_rls import get_db_rls
from app.db.models.ainvoaic.i_payment_method import PaymentMethodDB
from app.schemas.sch_payment_method import PaymentMethodCreate, PaymentMethodOut
from app.service.ser_payment_method import (
    create_or_update_payment_method,
    fetch_payment_methods,
)

pmRou = APIRouter()


def _to_out(method: PaymentMethodDB) -> PaymentMethodOut:
    return PaymentMethodOut(
        id=method.id,
        pm_name=method.pm_name,
        pm_note=method.pm_note,
    )


@pmRou.get("/get_pm_list", response_model=list[PaymentMethodOut])
async def get_payment_methods(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    methods = await fetch_payment_methods(zuid, db)
    return [_to_out(method) for method in methods]


@pmRou.post("/post_pm", response_model=PaymentMethodOut)
async def post_payment_method(
    payload: PaymentMethodCreate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    method = await create_or_update_payment_method(
        zuid, db, payload.model_dump(exclude_unset=True)
    )
    return _to_out(method)
