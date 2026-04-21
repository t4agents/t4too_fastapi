from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import HTTPException, status

from app.config import get_settings_singleton


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Any:
    settings = get_settings_singleton()
    service_key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
    if not service_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase service role key missing.",
        )

    try:
        from supabase import ClientOptions
        from supabase import create_client
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing Supabase SDK dependency. Install 'supabase'.",
        ) from exc

    auth_iss = settings.JWKS_ISS.rstrip("/")
    supabase_url = auth_iss[: -len("/auth/v1")] if auth_iss.endswith("/auth/v1") else auth_iss
    return create_client(
        supabase_url,
        service_key,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )
