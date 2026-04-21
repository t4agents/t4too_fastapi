from __future__ import annotations

import logging
from typing import Any
from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.inv.i_fee import FeeDB
from app.db.models.inv.i_nvoice import InvoiceDB
from app.db.models.inv.i_nvoice_item import InvoiceItemDB
from app.db.models.inv.i_nvoice_payment import InvoicePaymentDB
from app.db.models.inv.i_payment_method import PaymentMethodDB
from app.db.models.inv.i_tax import TaxDB
from app.db.models.inv.i_tem import ItemDB
from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_client import ZClientDB
from app.db.repo.repo_userprofile import get_user_by_id
from app.db.seed_catalog import (
    BIZ_DEFAULTS,
    CLIENT_TEMPLATES,
    FEE_TEMPLATES,
    INVOICE_TEMPLATES,
    ITEM_TEMPLATES,
    PAYMENT_METHOD_TEMPLATES,
    SEED_VERSION,
    TAX_TEMPLATES,
)

SEED_NAMESPACE = UUID("a9c57b13-0f0b-4ef2-b154-27b5957b08db")
_log = logging.getLogger(__name__)


def _seed_uuid(zjwt: dict, seed_key: str) -> UUID:
    return uuid5(SEED_NAMESPACE, f"{zuid}:{seed_key}")


def _seed_extra(seed_key: str) -> dict[str, Any]:
    return {
        "seed_managed": True,
        "seed_key": seed_key,
        "seed_version": SEED_VERSION,
    }


def _base_ids(zjwt: dict) -> dict[str, Any]:
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
    zjwt: dict,
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
    zjwt: dict,
    db: AsyncSession,
    *,
    reset: bool = False,
) -> dict[str, Any]:
    _log.info("seed apply start sub=%s reset=%s", zuid, reset)
    user = await get_user_by_id(db, zjwt["zuid"])
    email = user.email if user and user.email else "invoaice@gmail.com"
    display_name = user.display_name if user and user.display_name else "My Business Owner"
    _log.info(
        "seed user context sub=%s user_found=%s email=%s display_name=%s",
        zuid,
        bool(user),
        email,
        display_name,
    )

    base_ids = _base_ids(zjwt)
    summary: dict[str, Any] = {
        "seed_version": SEED_VERSION,
        "tables": {
            "biz": {"created": 0, "updated": 0, "deleted": 0},
            "clients": {"created": 0, "updated": 0, "deleted": 0},
            "items": {"created": 0, "updated": 0, "deleted": 0},
            "payment_methods": {"created": 0, "updated": 0, "deleted": 0},
            "fees": {"created": 0, "updated": 0, "deleted": 0},
            "taxes": {"created": 0, "updated": 0, "deleted": 0},
            "invoices": {"created": 0, "updated": 0, "deleted": 0},
            "invoice_items": {"created": 0, "updated": 0, "deleted": 0},
            "invoice_payments": {"created": 0, "updated": 0, "deleted": 0},
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
            "id": _seed_uuid(zjwt, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        client_rows.append(row)

    item_rows: list[dict[str, Any]] = []
    for template in ITEM_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zjwt, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        item_rows.append(row)

    payment_rows: list[dict[str, Any]] = []
    for template in PAYMENT_METHOD_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zjwt, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        payment_rows.append(row)

    fee_rows: list[dict[str, Any]] = []
    for template in FEE_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zjwt, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        fee_rows.append(row)

    tax_rows: list[dict[str, Any]] = []
    for template in TAX_TEMPLATES:
        seed_key = str(template["seed_key"])
        row = {
            "id": _seed_uuid(zjwt, seed_key),
            **base_ids,
            **{k: v for k, v in template.items() if k != "seed_key"},
            "extra": _seed_extra(seed_key),
        }
        tax_rows.append(row)

    client_by_seed_key = {str(t["seed_key"]): r for t, r in zip(CLIENT_TEMPLATES, client_rows)}
    item_by_seed_key = {str(t["seed_key"]): r for t, r in zip(ITEM_TEMPLATES, item_rows)}
    pm_by_seed_key = {str(t["seed_key"]): r for t, r in zip(PAYMENT_METHOD_TEMPLATES, payment_rows)}

    invoice_rows: list[dict[str, Any]] = []
    invoice_item_rows: list[dict[str, Any]] = []
    invoice_payment_rows: list[dict[str, Any]] = []
    for inv_template in INVOICE_TEMPLATES:
        inv_seed_key = str(inv_template["seed_key"])
        inv_id = _seed_uuid(zjwt, inv_seed_key)
        inv_client = client_by_seed_key[str(inv_template["client_seed_key"])]

        invoice_row = {
            "id": inv_id,
            **base_ids,
            "inv_number": inv_template["inv_number"],
            "inv_date": inv_template["inv_date"],
            "inv_due_date": inv_template["inv_due_date"],
            "inv_title": inv_template["inv_title"],
            "inv_reference": inv_template["inv_reference"],
            "inv_currency": inv_template["inv_currency"],
            "inv_payment_requirement": inv_template["inv_payment_requirement"],
            "inv_payment_term": inv_template["inv_payment_term"],
            "inv_subtotal": inv_template["inv_subtotal"],
            "inv_discount": inv_template["inv_discount"],
            "inv_tax_label": inv_template["inv_tax_label"],
            "inv_tax_rate": inv_template["inv_tax_rate"],
            "inv_tax_amount": inv_template["inv_tax_amount"],
            "inv_shipping": inv_template["inv_shipping"],
            "inv_handling": inv_template["inv_handling"],
            "inv_deposit": inv_template["inv_deposit"],
            "inv_adjustment": inv_template["inv_adjustment"],
            "inv_other_charges_label": inv_template["inv_other_charges_label"],
            "inv_other_charges_amount": inv_template["inv_other_charges_amount"],
            "inv_total": inv_template["inv_total"],
            "inv_paid_total": inv_template["inv_paid_total"],
            "inv_balance_due": inv_template["inv_balance_due"],
            "inv_payment_status": inv_template["inv_payment_status"],
            "inv_flag_word": inv_template["inv_flag_word"],
            "inv_flag_emoji": inv_template["inv_flag_emoji"],
            "inv_pdf_template": inv_template["inv_pdf_template"],
            "inv_notes": inv_template["inv_notes"],
            "inv_terms_conditions": inv_template["inv_terms_conditions"],
            "client_id": inv_client["id"],
            "client_number": inv_client.get("client_number"),
            "client_company_name": inv_client.get("client_company_name"),
            "client_contact_name": inv_client.get("client_contact_name"),
            "client_contact_title": inv_client.get("client_contact_title"),
            "client_address": inv_client.get("client_address"),
            "client_email": inv_client.get("client_email"),
            "client_secondphone": inv_client.get("client_secondphone"),
            "client_mainphone": inv_client.get("client_mainphone"),
            "client_fax": inv_client.get("client_fax"),
            "client_website": inv_client.get("client_website"),
            "client_business_number": inv_client.get("client_business_number"),
            "client_currency": inv_client.get("client_currency"),
            "client_tax_id": inv_client.get("client_tax_id"),
            "client_payment_term": inv_client.get("client_payment_term"),
            "client_payment_method": inv_client.get("client_payment_method"),
            "client_terms_conditions": inv_client.get("client_terms_conditions"),
            "client_note": inv_client.get("client_note"),
            "extra": _seed_extra(inv_seed_key),
        }
        invoice_rows.append(invoice_row)

        for idx, item_template in enumerate(inv_template["items"], start=1):
            item_seed_key = str(item_template["item_seed_key"])
            inv_item_seed_key = f"{inv_seed_key}:item:{idx}"
            seed_item = item_by_seed_key[item_seed_key]
            invoice_item_rows.append(
                {
                    "id": _seed_uuid(zjwt, inv_item_seed_key),
                    **base_ids,
                    "inv_id": inv_id,
                    "item_id": seed_item["id"],
                    "item_number": seed_item.get("item_number"),
                    "item_name": seed_item.get("item_name"),
                    "item_rate": item_template["item_rate"],
                    "item_unit_of_measure": seed_item.get("item_unit_of_measure"),
                    "item_unit": seed_item.get("item_unit"),
                    "item_sku": seed_item.get("item_sku"),
                    "item_description": seed_item.get("item_description"),
                    "item_quantity": item_template["item_quantity"],
                    "item_note": item_template.get("item_note"),
                    "item_amount": item_template["item_amount"],
                    "extra": _seed_extra(inv_item_seed_key),
                }
            )

        for pay_template in inv_template["payments"]:
            pay_seed_key = str(pay_template["payment_seed_key"])
            pay_method = pm_by_seed_key[str(pay_template["payment_method_seed_key"])]
            invoice_payment_rows.append(
                {
                    "id": _seed_uuid(zjwt, pay_seed_key),
                    **base_ids,
                    "inv_id": inv_id,
                    "pm_id": pay_method["id"],
                    "pm_name": pay_method.get("pm_name"),
                    "pm_note": pay_method.get("pm_note"),
                    "pay_date": pay_template["pay_date"],
                    "pay_amount": pay_template["pay_amount"],
                    "pay_reference": pay_template.get("pay_reference"),
                    "pay_note": pay_template.get("pay_note"),
                    "extra": _seed_extra(pay_seed_key),
                }
            )
    _log.info(
        "seed catalog counts sub=%s biz=%s clients=%s items=%s payment_methods=%s fees=%s taxes=%s invoices=%s invoice_items=%s invoice_payments=%s",
        zuid,
        1,
        len(client_rows),
        len(item_rows),
        len(payment_rows),
        len(fee_rows),
        len(tax_rows),
        len(invoice_rows),
        len(invoice_item_rows),
        len(invoice_payment_rows),
    )

    async def _run_seed_ops() -> None:
        if reset:
            _log.info("seed reset enabled sub=%s", zjwt["zuid"])
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
            summary["tables"]["invoices"]["deleted"] = await _delete_rows_by_ids(
                db, InvoiceDB, zuid, [row["id"] for row in invoice_rows]
            )
            summary["tables"]["invoice_items"]["deleted"] = await _delete_rows_by_ids(
                db, InvoiceItemDB, zuid, [row["id"] for row in invoice_item_rows]
            )
            summary["tables"]["invoice_payments"]["deleted"] = await _delete_rows_by_ids(
                db, InvoicePaymentDB, zuid, [row["id"] for row in invoice_payment_rows]
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

        created, updated = await _upsert_rows(db, InvoiceDB, invoice_rows, "invoices")
        summary["tables"]["invoices"]["created"] = created
        summary["tables"]["invoices"]["updated"] = updated

        created, updated = await _upsert_rows(db, InvoiceItemDB, invoice_item_rows, "invoice_items")
        summary["tables"]["invoice_items"]["created"] = created
        summary["tables"]["invoice_items"]["updated"] = updated

        created, updated = await _upsert_rows(db, InvoicePaymentDB, invoice_payment_rows, "invoice_payments")
        summary["tables"]["invoice_payments"]["created"] = created
        summary["tables"]["invoice_payments"]["updated"] = updated

    if db.in_transaction():
        _log.info("seed txn mode=subtransaction sub=%s", zjwt["zuid"])
        await _run_seed_ops()
    else:
        _log.info("seed txn mode=new_transaction sub=%s", zjwt["zuid"])
        async with db.begin():
            await _run_seed_ops()

    _log.info("seed apply complete sub=%s reset=%s summary=%s", zuid, reset, summary)
    return summary
