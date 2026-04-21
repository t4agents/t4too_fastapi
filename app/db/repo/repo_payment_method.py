from __future__ import annotations

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.db.models.inv.i_payment_method import PaymentMethodDB
from app.db.repo.repo_utils import coerce_model_values

_log = logging.getLogger("app.http")


async def _read_rls_context(db: AsyncSession) -> dict:
    result = await db.execute(
        text(
            "select "
            "current_user::text as current_user, "
            "session_user::text as session_user, "
            "current_setting('role', true)::text as active_role, "
            "auth.jwt() ->> 'sub' as jwt_sub, "
            "auth.jwt() ->> 'sba_ten_id' as jwt_ten_id"
        )
    )
    row = result.mappings().one()
    return dict(row)


async def _read_payment_method_snapshot(
    db: AsyncSession, method_id: UUID
) -> Optional[dict]:
    result = await db.execute(
        text(
            "select "
            "id::text as id, "
            "ten_id::text as ten_id, "
            "created_by::text as created_by, "
            "pm_name::text as pm_name "
            "from too_inv.ipayment_method "
            "where id = :method_id"
        ),
        {"method_id": str(method_id)},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def list_payment_methods(db: AsyncSession, actor_id: UUID) -> List[PaymentMethodDB]:
    ctx = await _read_rls_context(db)
    _log.info("pm.list start actor_id=%s rls_ctx=%s", actor_id, ctx)
    result = await db.execute(
        select(PaymentMethodDB)
        .where(PaymentMethodDB.created_by == actor_id)
        .order_by(PaymentMethodDB.created_at.desc())
    )
    rows = list(result.scalars().all())
    _log.info("pm.list done actor_id=%s count=%s", actor_id, len(rows))
    return rows


async def get_payment_method_by_id(
    db: AsyncSession, method_id: UUID, actor_id: UUID
) -> Optional[PaymentMethodDB]:
    ctx = await _read_rls_context(db)
    _log.info(
        "pm.get_by_id start method_id=%s actor_id=%s rls_ctx=%s",
        method_id,
        actor_id,
        ctx,
    )
    result = await db.execute(
        select(PaymentMethodDB).where(
            PaymentMethodDB.id == method_id,
            PaymentMethodDB.created_by == actor_id,
        )
    )
    row = result.scalar_one_or_none()
    _log.info(
        "pm.get_by_id done method_id=%s actor_id=%s found=%s found_ten_id=%s found_created_by=%s",
        method_id,
        actor_id,
        bool(row),
        str(row.ten_id) if row else None,
        str(row.created_by) if row else None,
    )
    return row


async def create_payment_method(db: AsyncSession, payload: dict) -> PaymentMethodDB:
    method = PaymentMethodDB(**coerce_model_values(PaymentMethodDB, payload))
    db.add(method)
    await db.commit()
    return method


async def update_payment_method_fields(
    db: AsyncSession,
    method: PaymentMethodDB,
    updates: dict,
    actor_id: UUID,
    expected_ten_id: UUID | str,
) -> PaymentMethodDB:
    if updates:
        for key, value in coerce_model_values(method, updates).items():
            setattr(method, key, value)
        db.add(method)
        try:
            await db.commit()
        except StaleDataError:
            try:await db.rollback()
            except InvalidRequestError:raise
    return method
