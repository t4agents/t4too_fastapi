from __future__ import annotations

from uuid import UUID
from .supabase_admin import get_supabase_admin_client


async def updateid_ten_cli(uid: UUID|None) -> None:
    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(str(uid),
            {"app_metadata": {"sba_ten_id": str(uid)},
             "user_metadata": {"sbu_client_id": str(uid),},},
        )
    except Exception: raise
