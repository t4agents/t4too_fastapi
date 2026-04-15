from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ainvoaic.i_fee import FeeDB
from app.db.models.ainvoaic.i_payment_method import PaymentMethodDB
from app.db.models.ainvoaic.i_tax import TaxDB
from app.db.models.ainvoaic.i_tem import ItemDB
from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_client import ZClientDB
from app.db.repo.repo_userprofile import get_user_by_id
from app.db.seed_catalog import (
    BIZ_DEFAULTS,
    CLIENT_TEMPLATES,
    FEE_TEMPLATES,
    ITEM_TEMPLATES,
    PAYMENT_METHOD_TEMPLATES,
    SEED_VERSION,
    TAX_TEMPLATES,
)

SEED_NAMESPACE = UUID("a9c57b13-0f0b-4ef2-b154-27b5957b08db")
_log = logging.getLogger(__name__)


def _seed_uuid(zuid: UUID, seed_key: str) -> UUID:
    return uuid5(SEED_NAMESPACE, f"{zuid}:{seed_key}")


def _seed_extra(seed_key: str) -> dict[str, Any]:
    return {
        "seed_managed": True,
        "seed_key": seed_key,
        "seed_version": SEED_VERSION,
    }


def _base_ids(zuid: UUID) -> dict[str, Any]:
    return {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }


async def _find_existing_ids(db: AsyncSession, model: Any, ids: list[UUID]) -> set[UUID]:
    if not ids:
        return set()
    result = await db.execute(select(model.id).where(model.id.in_(ids)))
    existing = set(result.scalars().all())
    _log.info(
        "seed existing scan model=%s input_ids=%s existing_ids=%s",
        model.__name__,
        len(ids),
        len(existing),
    )
    return existing


async def _upsert_rows(
    db: AsyncSession,
    model: Any,
    rows: list[dict[str, Any]],
    label: str,
) -> tuple[int, int]:
    if not rows:
        _log.info("seed upsert skipped table=%s reason=no_rows", label)
        return 0, 0

    ids = [row["id"] for row in rows]
    existing_ids = await _find_existing_ids(db, model, ids)

    stmt = insert(model).values(rows)
    update_map = {
        key: getattr(stmt.excluded, key)
        for key in rows[0].keys()
        if key not in {"id", "created_at"}
    }
    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_=update_map)
    await db.execute(stmt)

    updated = len(existing_ids)
    created = len(rows) - updated
    _log.info(
        "seed upsert table=%s rows=%s created=%s updated=%s",
        label,
        len(rows),
        created,
        updated,
    )
    return created, updated


async def _delete_rows_by_ids(
    db: AsyncSession,
    model: Any,
    zuid: UUID,
    ids: list[UUID],
) -> int:
    if not ids:
        _log.info("seed delete skipped model=%s reason=no_ids", model.__name__)
        return 0
    stmt = (
        delete(model)
        .where(
        model.created_by == zuid,
        model.id.in_(ids),
    )
        .returning(model.id)
    )
    result = await db.execute(stmt)
    deleted = len(result.scalars().all())
    _log.info(
        "seed delete model=%s ids_requested=%s deleted=%s",
        model.__name__,
        len(ids),
        deleted,
    )
    return deleted


async def apply_seed_defaults(
    zuid: UUID,
    db: AsyncSession,
    *,
    reset: bool = False,
) -> dict[str, Any]:
    _log.info("seed apply start sub=%s reset=%s", zuid, reset)
    user = await get_user_by_id(db, zuid)
    email = user.email if user and user.email else "invoaice@gmail.com"
    display_name = user.display_name if user and user.display_name else "My Business Owner"
    _log.info(
        "seed user context sub=%s user_found=%s email=%s display_name=%s",
        zuid,
        bool(user),
        email,
        display_name,
    )

    base_ids = _base_ids(zuid)
    summary: dict[str, Any] = {
        "seed_version": SEED_VERSION,
        "tables": {
            "biz": {"created": 0, "updated": 0, "deleted": 0},
            "clients": {"created": 0, "updated": 0, "deleted": 0},
            "items": {"created": 0, "updated": 0, "deleted": 0},
            "payment_methods": {"created": 0, "updated": 0, "deleted": 0},
            "fees": {"created": 0, "updated": 0, "deleted": 0},
            "taxes": {"created": 0, "updated": 0, "deleted": 0},
        },
    }

    be_row = {
        "id": zuid,
        **base_ids,
        "be_name": BIZ_DEFAULTS.be_name,
        "be_type": BIZ_DEFAULTS.be_type,
        "be_email": email,
        "be_phone": "332-203-4114",
        "be_contact": display_name,
        "be_currency": BIZ_DEFAULTS.be_currency,
        "be_payment_term": BIZ_DEFAULTS.be_payment_term,
        "be_inv_prefix": BIZ_DEFAULTS.be_inv_prefix,
        "be_inv_integer": BIZ_DEFAULTS.be_inv_integer,
        "be_inv_integer_max": BIZ_DEFAULTS.be_inv_integer_max,
        "be_date_format": BIZ_DEFAULTS.be_date_format,
        "be_timezone": BIZ_DEFAULTS.be_timezone,
        "extra": _seed_extra("biz_default"),
    }

    client_rows: list[dict[str, Any]] = []
    for template in CLIENT_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zuid, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        client_rows.append(row)

    item_rows: list[dict[str, Any]] = []
    for template in ITEM_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zuid, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        item_rows.append(row)

    payment_rows: list[dict[str, Any]] = []
    for template in PAYMENT_METHOD_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zuid, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        payment_rows.append(row)

    fee_rows: list[dict[str, Any]] = []
    for template in FEE_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zuid, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        fee_rows.append(row)

    tax_rows: list[dict[str, Any]] = []
    for template in TAX_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zuid, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        tax_rows.append(row)
    _log.info(
        "seed catalog counts sub=%s biz=%s clients=%s items=%s payment_methods=%s fees=%s taxes=%s",
        zuid,
        1,
        len(client_rows),
        len(item_rows),
        len(payment_rows),
        len(fee_rows),
        len(tax_rows),
    )

    async def _run_seed_ops() -> None:
        if reset:
            _log.info("seed reset enabled sub=%s", zuid)
            summary["tables"]["clients"]["deleted"] = await _delete_rows_by_ids(
                db, ZClientDB, zuid, [row["id"] for row in client_rows]
            )
            summary["tables"]["items"]["deleted"] = await _delete_rows_by_ids(
                db, ItemDB, zuid, [row["id"] for row in item_rows]
            )
            summary["tables"]["payment_methods"]["deleted"] = await _delete_rows_by_ids(
                db, PaymentMethodDB, zuid, [row["id"] for row in payment_rows]
            )
            summary["tables"]["fees"]["deleted"] = await _delete_rows_by_ids(
                db, FeeDB, zuid, [row["id"] for row in fee_rows]
            )
            summary["tables"]["taxes"]["deleted"] = await _delete_rows_by_ids(
                db, TaxDB, zuid, [row["id"] for row in tax_rows]
            )

        created, updated = await _upsert_rows(db, ZBizEntityDB, [be_row], "biz")
        summary["tables"]["biz"]["created"] = created
        summary["tables"]["biz"]["updated"] = updated

        created, updated = await _upsert_rows(db, ZClientDB, client_rows, "clients")
        summary["tables"]["clients"]["created"] = created
        summary["tables"]["clients"]["updated"] = updated

        created, updated = await _upsert_rows(db, ItemDB, item_rows, "items")
        summary["tables"]["items"]["created"] = created
        summary["tables"]["items"]["updated"] = updated

        created, updated = await _upsert_rows(db, PaymentMethodDB, payment_rows, "payment_methods")
        summary["tables"]["payment_methods"]["created"] = created
        summary["tables"]["payment_methods"]["updated"] = updated

        created, updated = await _upsert_rows(db, FeeDB, fee_rows, "fees")
        summary["tables"]["fees"]["created"] = created
        summary["tables"]["fees"]["updated"] = updated

        created, updated = await _upsert_rows(db, TaxDB, tax_rows, "taxes")
        summary["tables"]["taxes"]["created"] = created
        summary["tables"]["taxes"]["updated"] = updated

    if db.in_transaction():
        _log.info("seed txn mode=subtransaction sub=%s", zuid)
        await _run_seed_ops()
    else:
        _log.info("seed txn mode=new_transaction sub=%s", zuid)
        async with db.begin():
            await _run_seed_ops()

    _log.info("seed apply complete sub=%s reset=%s summary=%s", zuid, reset, summary)
    return summary
