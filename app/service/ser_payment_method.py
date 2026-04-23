from __future__ import annotations

import logging
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

_log = logging.getLogger("app.http")


async def fetch_payment_methods(zjwt: JWType, db: AsyncSession) -> list[PaymentMethodDB]:
    _log.info(
        "pm.service.list zuid=%s jwt_ten_id=%s",
        zjwt.get("zuid"),
        (zjwt.get("app_metadata") or {}).get("sba_ten_id"),
    )
    return await list_payment_methods(db, zjwt["zuid"])


async def create_or_update_payment_method(
    zjwt: JWType, db: AsyncSession, payload: dict
) -> PaymentMethodDB:
    jwt_ten_id = (zjwt.get("app_metadata") or {}).get("sba_ten_id")
    _log.info(
        "pm.service.upsert start zuid=%s jwt_ten_id=%s payload=%s",
        zjwt.get("zuid"),
        jwt_ten_id,
        payload,
    )
    base_ids = {
        "ten_id": jwt_ten_id,
        "biz_id": zjwt["zuid"],
        "usr_id": zjwt["zuid"],
        "cli_id": zjwt["zuid"],
        "created_by": zjwt["zuid"],
    }
    method_id = payload.get("id")
    if method_id:
        _log.info(
            "pm.service.upsert update-attempt method_id=%s zuid=%s jwt_ten_id=%s",
            method_id,
            zjwt.get("zuid"),
            jwt_ten_id,
        )
        existing = await get_payment_method_by_id(db, method_id, zjwt["zuid"])
        updates = {k: v for k, v in payload.items() if k != "id"}
        if existing:
            _log.info(
                "pm.service.upsert existing-found method_id=%s existing_ten_id=%s existing_created_by=%s updates=%s",
                existing.id,
                existing.ten_id,
                existing.created_by,
                updates,
            )
            return await update_payment_method_fields(
                db,
                existing,
                updates,
                actor_id=zjwt["zuid"],
                expected_ten_id=jwt_ten_id,
            )
        _log.warning(
            "pm.service.upsert existing-not-found method_id=%s zuid=%s",
            method_id,
            zjwt.get("zuid"),
        )
    data = {**base_ids, **payload}
    _log.info(
        "pm.service.upsert create-attempt ten_id=%s created_by=%s payload_keys=%s",
        data.get("ten_id"),
        data.get("created_by"),
        sorted(data.keys()),
    )
    return await repo_create_payment_method(db, data)
