from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_nvoice import InvoiceDB
from app.db.models.inv.i_nvoice_item import InvoiceItemDB
from app.db.models.inv.i_nvoice_payment import InvoicePaymentDB
from app.db.repo.repo_inv_item import list_invoice_items
from app.db.repo.repo_inv import (create_invoice,get_invoice_by_id,list_invoices,update_invoice_fields,)
from app.db.repo.repo_inv_payment import (create_invoice_payment,list_invoice_payments,)

_INVOICE_COLUMNS = set(InvoiceDB.__table__.columns.keys())
_INVOICE_PAYMENT_COLUMNS = set(InvoicePaymentDB.__table__.columns.keys())


@dataclass(slots=True)
class InvoiceAggregate:
    invoice: InvoiceDB
    items: list[InvoiceItemDB]
    payments: list[InvoicePaymentDB]


async def fetch_invoices(db: AsyncSession) -> list[InvoiceDB]:
    return await list_invoices(db)


def _to_uuid(value: Any) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y", "on"}
    return bool(value)


def _base_ids(zjwt: dict) -> dict[str, UUID]:
    return {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }


async def fetch_invoice_by_id(zjwt: dict, db: AsyncSession, inv_id: UUID) -> InvoiceAggregate | None:
    inv = await get_invoice_by_id(db, inv_id)
    if not inv:return None
    items, payments = await asyncio.gather(
        list_invoice_items(db, inv_id),
        list_invoice_payments(db, inv_id),
    )
    return InvoiceAggregate(invoice=inv, items=items, payments=payments)


async def create_or_update_invoice(zjwt: dict, db: AsyncSession, payload: dict) -> InvoiceDB:
    data = dict(payload)
    inv_id = _to_uuid(data.pop("inv_id", None) or data.get("id"))
    if inv_id:
        data["id"] = inv_id

    if "be_id" in data and "biz_id" not in data:
        data["biz_id"] = data.pop("be_id")
    if "user_id" in data and "usr_id" not in data:
        data["usr_id"] = data.pop("user_id")
    if "is_locked" in data:
        data["is_flag"] = _to_bool(data.pop("is_locked"))
    if "is_deleted" in data:
        data["is_deleted"] = _to_bool(data.get("is_deleted"))

    data.pop("is_active", None)
    data.pop("inv_items", None)
    data.pop("inv_payments", None)
    data.pop("created_at", None)
    data.pop("updated_at", None)

    filtered = {k: v for k, v in data.items() if k in _INVOICE_COLUMNS}
    inv_id = _to_uuid(filtered.get("id"))
    if inv_id:
        existing = await get_invoice_by_id(db, inv_id, zjwt["zuid"])
        if existing:
            updates = {
                k: v
                for k, v in filtered.items()
                if k
                not in {
                    "id",
                    "ten_id",
                    "biz_id",
                    "usr_id",
                    "cli_id",
                    "created_by",
                    "created_at",
                }
            }
            return await update_invoice_fields(db, existing, updates)

    create_payload = {**_base_ids(zjwt["zuid"]), **filtered}
    return await create_invoice(db, create_payload)


async def fetch_invoice_payments(db: AsyncSession, inv_id: UUID) -> list[InvoicePaymentDB]:
    return await list_invoice_payments(db, inv_id)


async def create_inv_payment(db: AsyncSession, payload: dict, zjwt: dict, ten_id: UUID) -> InvoicePaymentDB:
    data = dict(payload)

    inv_id = _to_uuid(data.get("inv_id"))
    if not inv_id:
        raise ValueError("inv_id is required and must be a valid UUID")
    data["inv_id"] = inv_id

    # Payment creation is owned by JWT context, not request payload.
    data.pop("id", None)
    data.pop("payment_id", None)
    data.pop("ten_id", None)
    data.pop("biz_id", None)
    data.pop("usr_id", None)
    data.pop("created_by", None)

    data["pm_id"] = _to_uuid(data.get("pm_id"))
    if "is_locked" in data:
        data["is_flag"] = _to_bool(data.pop("is_locked"))
    if "is_deleted" in data:
        data["is_deleted"] = _to_bool(data.get("is_deleted"))

    data.pop("is_active", None)
    data.pop("updated_at", None)

    filtered = {k: v for k, v in data.items() if k in _INVOICE_PAYMENT_COLUMNS}
    create_payload = {
        **filtered,
        "ten_id": ten_id,
        "biz_id": ten_id,
        "usr_id": zuid,
        "created_by": zuid,
    }
    return await create_invoice_payment(db, create_payload)
