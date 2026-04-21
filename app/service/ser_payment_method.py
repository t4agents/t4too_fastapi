from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_payment_method import PaymentMethodDB
from app.db.repo.repo_payment_method import (
    create_payment_method as repo_create_payment_method,
)
from app.db.repo.repo_payment_method import (
    get_payment_method_by_id,
    list_payment_methods,
    update_payment_method_fields,
)


async def fetch_payment_methods(db: AsyncSession) -> list[PaymentMethodDB]:
    return await list_payment_methods(db)


async def create_or_update_payment_method(
    zjwt: dict, db: AsyncSession, payload: dict
) -> PaymentMethodDB:
    base_ids = {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }
    method_id = payload.get("id")
    if method_id:
        existing = await get_payment_method_by_id(db, method_id, zjwt["zuid"])
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            return await update_payment_method_fields(db, existing, updates)
    data = {**base_ids, **payload}
    return await repo_create_payment_method(db, data)
