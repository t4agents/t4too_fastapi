from __future__ import annotations

from uuid import UUID

from app.schemas.sch_ai import JWType
from app.schemas.sch_userprofile import UserProfileUpdate
from .supabase_admin import get_supabase_admin_client


async def updateid_ten_cli(uid: UUID|None) -> None:
    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(str(uid),
            {"app_metadata": {"sba_ten_id": str(uid)},
             "user_metadata": {"sbu_client_id": str(uid),},},
        )
    except Exception: raise



async def update_sbu_be(zjwt: JWType, be_name: str | None) -> None:
    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(str(zjwt.zuid),
            {"user_metadata": {"sbu_be_name": be_name},},
        )
    except Exception: raise



async def update_sbu_me(zjwt: JWType, payload:UserProfileUpdate) -> None:
    supabase = get_supabase_admin_client()
    try:
        supabase.auth.admin.update_user_by_id(str(zjwt.zuid),
            {"user_metadata": {"sbu_user_avatar": payload.avatar},},
        )
    except Exception: raise
