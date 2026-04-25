from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.supabase_meta import updateid_ten_cli
from app.db.seed.new_user_defaults import NEW_USER_DEFAULTS, default_payroll_schedule_templates
from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_client import ZClientDB
from app.db.models.too.z_user import ZUserDB
from app.db.models.too.z_user_client import ZUserClientDB
from app.schemas.sch_ai import JWType
from app.service.ser_seed import apply_seed_defaults


async def _ensure_default_payroll_schedules(
    db: AsyncSession,
    *,
    ten_id: UUID|None,
    cli_id: UUID|None,
    usr_id: UUID|None,
    created_by: UUID|None,
) -> None:
    for template in default_payroll_schedule_templates():
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



async def provision_new_user_with_seed(zjwt: JWType, db: AsyncSession) -> None:
    zuid = zjwt.zuid    
    zemail = zjwt.zemail or NEW_USER_DEFAULTS["email"]
    sbu_user_type = zjwt.user_metadata.get("sbu_user_type")

    display_name = zjwt.user_metadata.get("sbu_user_name") or zjwt.user_metadata.get("sbu_name") or NEW_USER_DEFAULTS["name"]

    base_ids = {
        "id": zuid,
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }

    zuser_payload = {
        **base_ids,
        "email": zemail,
        "display_name": display_name,
        "name": display_name,
        "usr_type": sbu_user_type,
        "full_name": display_name,
        "first_name": display_name,
        "last_name": display_name,
        "avatar": zjwt.user_metadata.get("sbu_user_avatar") or NEW_USER_DEFAULTS["avatar"],
        "phone": NEW_USER_DEFAULTS["phone"],
        "position": NEW_USER_DEFAULTS["position"],
        "facebook": NEW_USER_DEFAULTS["facebook"],
        "twitter": NEW_USER_DEFAULTS["twitter"],
        "github": NEW_USER_DEFAULTS["github"],
        "reddit": NEW_USER_DEFAULTS["reddit"],
        "country": NEW_USER_DEFAULTS["country"],
        "state": NEW_USER_DEFAULTS["state"],
        "pin": NEW_USER_DEFAULTS["pin"],
        "zip": NEW_USER_DEFAULTS["zip"],
        "tax_no": NEW_USER_DEFAULTS["taxNo"],
    }

    zbe_payload = {
        **base_ids,
        "be_name": "My Business",
        "be_type": "ME",
        "be_email": zemail,
        "be_phone": NEW_USER_DEFAULTS["phone"],
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
                ten_id=zuid,
                cli_id=zuid,
                usr_id=zuid,
                created_by=zuid,
            )
            seed_summary = await apply_seed_defaults(zuid=zuid, db=db, reset=False)
    except Exception:        raise
    await updateid_ten_cli(zuid)
