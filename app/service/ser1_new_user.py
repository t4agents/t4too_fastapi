from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_admin import get_supabase_admin_client
from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_client import ZClientDB
from app.db.models.too.z_user import ZUserDB
from app.db.models.too.z_user_client import ZUserClientDB
from app.service.ser_seed import apply_seed_defaults

_log = logging.getLogger(__name__)

DEFAULTS = {
    "email": "invoaice@gmail.com",
    "name": "Invoaice Agents",
    "usr_type": "usr_type",
    "firstName": "Invoaice",
    "lastName": "Agents",
    "phone": "332-203-4114",
    "position": "CPA",
    "facebook": "https://facebook.com/invoaice",
    "twitter": "https://twitter.com/invoaice",
    "github": "https://github.com/invoaice",
    "reddit": "https://reddit.com/u/invoaice",
    "country": "Canada",
    "state": "Ontario",
    "pin": "3322034114",
    "zip": "M5V 2T6",
    "taxNo": "invoaice123",
}

def _to_name_parts(full_name: str | None) -> Dict[str, str]:
    safe_name = (full_name or "").strip() or DEFAULTS["name"]
    parts = [part for part in safe_name.split(" ") if part]
    first = parts[0] if parts else DEFAULTS["firstName"]
    last = " ".join(parts[1:]) if len(parts) > 1 else DEFAULTS["lastName"]
    return {"fullName": safe_name, "firstName": first, "lastName": last}


def _email_to_display_name(email: str | None) -> str:
    if email and "@" in email:
        local = email.split("@", 1)[0].strip()
        if local:
            return local
    return DEFAULTS["name"]


def _extract_sbu_user_type(decoded: dict[str, Any]) -> str:
    user_metadata = decoded.get("user_metadata")
    if isinstance(user_metadata, dict):
        meta_value = user_metadata.get("sbu_user_type")
        if isinstance(meta_value, str) and meta_value.strip():
            return meta_value.strip()

    root_value = decoded.get("sbu_user_type")
    if isinstance(root_value, str) and root_value.strip():
        return root_value.strip()

    return "SBU"


def _default_payroll_schedule_templates() -> list[dict[str, Any]]:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    return [
        {
            "frequency": "weekly",
            "effective_from": week_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "Friday",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "Mon-Fri",
            "note": "From Monday to Friday.",
        },
        {
            "frequency": "biweekly",
            "effective_from": week_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "Friday",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "Mon-Fri (2 weeks)",
            "note": "Pays every other week.",
        },
        {
            "frequency": "semimonthly",
            "effective_from": month_start,
            "effective_to": date.max,
            "status": "inactive",
            "description": "Description",
            "payon": "EOM",
            "semi1": "15",
            "semi2": "EOM",
            "period": "1st-15th, 16th-EOM",
            "note": "Pays twice a month.",
        },
        {
            "frequency": "monthly",
            "effective_from": month_start,
            "effective_to": date.max,
            "status": "active",
            "description": "Description",
            "payon": "EOM",
            "semi1": "EOM",
            "semi2": "EOM",
            "period": "1st-EOM",
            "note": "Pays once a month.",
        },
    ]


async def _ensure_default_payroll_schedules(
    db: AsyncSession,
    *,
    ten_id: UUID,
    cli_id: UUID,
    usr_id: UUID,
    created_by: UUID,
) -> None:
    for template in _default_payroll_schedule_templates():
        existing_id = await db.scalar(
            select(PayrollScheduleDB.id).where(
                PayrollScheduleDB.cli_id == cli_id,
                PayrollScheduleDB.frequency == template["frequency"],
            )
        )
        if existing_id:
            continue
        db.add(
            PayrollScheduleDB(
                ten_id=ten_id,
                biz_id=cli_id,
                cli_id=cli_id,
                usr_id=usr_id,
                created_by=created_by,
                **template,
            )
        )


async def _update_supabase_app_metadata_ten_id(uid: UUID) -> None:
    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(
            str(uid),
            {"app_metadata": {"sba_ten_id": str(uid)}},
        )
    except Exception as exc:
        _log.error("supabase app_metadata update failed uid=%s err=%s", uid, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Supabase app_metadata update failed.",
        ) from exc


async def provision_new_user(decoded: dict, db: AsyncSession) -> None:
    # Supabase access tokens use "sub" as the user UUID
    user_id_raw = decoded.get("sub") or decoded.get("id")
    email = decoded.get("email") or DEFAULTS["email"]
    sbu_user_type = _extract_sbu_user_type(decoded)
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing user id.",
        )

    try:
        user_id = UUID(str(user_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT user id is not a valid UUID.",
        ) from exc

    display_name = _email_to_display_name(email)
    name_parts = _to_name_parts(display_name)

    base_ids = {
        "id": user_id,
        "ten_id": user_id,
        "biz_id": user_id,
        "usr_id": user_id,
        "cli_id": user_id,
        "created_by": user_id,
    }

    zuser_payload = {
        **base_ids,
        "email": email,
        "display_name": display_name,
        "name": display_name,
        "full_name": name_parts["fullName"],
        "first_name": name_parts["firstName"],
        "last_name": name_parts["lastName"],
        "avatar": None,
        "usr_type": sbu_user_type,
        "phone": DEFAULTS["phone"],
        "position": DEFAULTS["position"],
        "facebook": DEFAULTS["facebook"],
        "twitter": DEFAULTS["twitter"],
        "github": DEFAULTS["github"],
        "reddit": DEFAULTS["reddit"],
        "country": DEFAULTS["country"],
        "state": DEFAULTS["state"],
        "pin": DEFAULTS["pin"],
        "zip": DEFAULTS["zip"],
        "tax_no": DEFAULTS["taxNo"],
    }

    zbe_payload = {
        **base_ids,
        "be_name": "My Business",
        "be_type": "ME",
        "be_email": email,
        "be_phone": DEFAULTS["phone"],
        "be_contact": display_name,
        "be_logo": "https://raw.githubusercontent.com/ainvoaice/ainvoAIce/refs/heads/main/entrepreneurs.jpg",
    }

    zclient_payload = {
        **base_ids,
        "client_company_name": zbe_payload.get("be_name"),
        "client_contact_name": zbe_payload.get("be_contact"),
        "client_contact_title": zbe_payload.get("be_contact_title"),
        "client_address": zbe_payload.get("be_address"),
        "client_email": zbe_payload.get("be_email"),
        "client_mainphone": zbe_payload.get("be_phone"),
        "client_website": zbe_payload.get("be_website"),
        "client_tax_id": zbe_payload.get("be_tax_id"),
        "client_payment_term": zbe_payload.get("be_payment_term"),
        "client_currency": zbe_payload.get("be_currency"),
        "client_template_id": zbe_payload.get("be_inv_template_id"),
        "client_terms_conditions": zbe_payload.get("be_description"),
        "client_note": zbe_payload.get("be_note"),
    }

    z_user_client_payload = {**base_ids}


    try:
        async with db.begin():
            await db.execute(
                insert(ZUserDB)
                .values(**zuser_payload)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"usr_type": sbu_user_type},
                )
            )
            await db.execute(insert(ZBizEntityDB).values(**zbe_payload).on_conflict_do_nothing(index_elements=["id"]))
            await db.execute(insert(ZClientDB).values(**zclient_payload).on_conflict_do_nothing(index_elements=["id"]))
            await db.execute(insert(ZUserClientDB).values(**z_user_client_payload).on_conflict_do_nothing(index_elements=["id"]))
            await _ensure_default_payroll_schedules(
                db,
                ten_id=user_id,
                cli_id=user_id,
                usr_id=user_id,
                created_by=user_id,
            )
    except Exception:        raise
    await _update_supabase_app_metadata_ten_id(user_id)




async def provision_new_user_with_seed(decoded: dict, db: AsyncSession) -> None:
    user_id_raw = decoded.get("sub") or decoded.get("id")
    email = decoded.get("email") or DEFAULTS["email"]
    sbu_user_type = _extract_sbu_user_type(decoded)
    
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT missing user id.",
        )
    try:
        user_id = UUID(str(user_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT user id is not a valid UUID.",
        ) from exc

    display_name = _email_to_display_name(email)
    name_parts = _to_name_parts(display_name)

    base_ids = {
        "id": user_id,
        "ten_id": user_id,
        "biz_id": user_id,
        "usr_id": user_id,
        "cli_id": user_id,
        "created_by": user_id,
    }

    zuser_payload = {
        **base_ids,
        "email": email,
        "display_name": display_name,
        "name": display_name,
        "usr_type": sbu_user_type,
        "full_name": name_parts["fullName"],
        "first_name": name_parts["firstName"],
        "last_name": name_parts["lastName"],
        "avatar": None,
        "phone": DEFAULTS["phone"],
        "position": DEFAULTS["position"],
        "facebook": DEFAULTS["facebook"],
        "twitter": DEFAULTS["twitter"],
        "github": DEFAULTS["github"],
        "reddit": DEFAULTS["reddit"],
        "country": DEFAULTS["country"],
        "state": DEFAULTS["state"],
        "pin": DEFAULTS["pin"],
        "zip": DEFAULTS["zip"],
        "tax_no": DEFAULTS["taxNo"],
    }

    zbe_payload = {
        **base_ids,
        "be_name": "My Business",
        "be_type": "ME",
        "be_email": email,
        "be_phone": DEFAULTS["phone"],
        "be_contact": display_name,
        "be_logo": "https://raw.githubusercontent.com/ainvoaice/ainvoAIce/refs/heads/main/entrepreneurs.jpg",
    }

    zclient_payload = {
        **base_ids,
        "client_company_name": zbe_payload.get("be_name"),
        "client_contact_name": zbe_payload.get("be_contact"),
        "client_contact_title": zbe_payload.get("be_contact_title"),
        "client_address": zbe_payload.get("be_address"),
        "client_email": zbe_payload.get("be_email"),
        "client_mainphone": zbe_payload.get("be_phone"),
        "client_website": zbe_payload.get("be_website"),
        "client_tax_id": zbe_payload.get("be_tax_id"),
        "client_payment_term": zbe_payload.get("be_payment_term"),
        "client_currency": zbe_payload.get("be_currency"),
        "client_template_id": zbe_payload.get("be_inv_template_id"),
        "client_terms_conditions": zbe_payload.get("be_description"),
        "client_note": zbe_payload.get("be_note"),
    }

    z_user_client_payload = {**base_ids}

    try:
        async with db.begin():
            await db.execute(
                insert(ZUserDB)
                .values(**zuser_payload)
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={"usr_type": sbu_user_type},
                )
            )
            await db.execute(insert(ZBizEntityDB).values(**zbe_payload).on_conflict_do_nothing(index_elements=["id"]))
            await db.execute(insert(ZClientDB).values(**zclient_payload).on_conflict_do_nothing(index_elements=["id"]))
            await db.execute(insert(ZUserClientDB).values(**z_user_client_payload).on_conflict_do_nothing(index_elements=["id"]))
            await _ensure_default_payroll_schedules(
                db,
                ten_id=user_id,
                cli_id=user_id,
                usr_id=user_id,
                created_by=user_id,
            )
            seed_summary = await apply_seed_defaults(user_id, db, reset=False)
    except Exception:        raise
    await _update_supabase_app_metadata_ten_id(user_id)
