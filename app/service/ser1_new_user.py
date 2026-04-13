from __future__ import annotations

import logging
from typing import Dict
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_client import ZClientDB
from app.db.models.too.z_user import ZUserDB

DEFAULTS = {
    "email": "invoaice@gmail.com",
    "name": "Invoaice Agents",
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

_log = logging.getLogger(__name__)

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


async def provision_new_user(decoded: dict, db: AsyncSession) -> None:
    _log.info("provision_new_user start keys=%s", sorted(decoded.keys()))
    # Supabase access tokens use "sub" as the user UUID
    user_id_raw = decoded.get("sub") or decoded.get("id")
    email = decoded.get("email") or DEFAULTS["email"]
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

    z_user_client_payload = {
        **base_ids,
        "be_name": "My Business",
        "be_type": "ME",
        "be_email": email,
        "be_phone": DEFAULTS["phone"],
        "be_contact": display_name,
    }


    try:
        async with db.begin():
            await db.execute(
                insert(ZUserDB)
                    .values(**zuser_payload)
                    .on_conflict_do_nothing(index_elements=["id"])
                )
            await db.execute(
            insert(ZBizEntityDB)
            .values(**zbe_payload)
            .on_conflict_do_nothing(index_elements=["id"])
            )
            _log.info("provision_new_user z_be insert done")
            await db.execute(
            insert(ZClientDB)
            .values(**zclient_payload)
            .on_conflict_do_nothing(index_elements=["id"])
            )
            _log.info("provision_new_user z_client insert done")
    except Exception:
        _log.exception("provision_new_user db error")
        raise
    _log.info("provision_new_user complete")
