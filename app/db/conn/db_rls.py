# For other tables, the same pattern works if all 4 are true:

# Role context is set per request (SET LOCAL ROLE authenticated)
# JWT claims are set per request (request.jwt.claims) with required tenant keys
# DB privileges exist for that schema/table (USAGE on schema + table grants)
# RLS is enabled + policy exists on each table
# For each new table, do:

# ALTER TABLE ... ENABLE ROW LEVEL SECURITY
# CREATE POLICY ... FOR SELECT ... USING (...)
# Add INSERT/UPDATE/DELETE policies too (WITH CHECK for writes)
# So yes, apply similar policy logic table-by-table, and it will work with your current backend RLS setup.
import json
import logging
import re
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError as SQLAlchemyProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings_singleton
from app.core.auth import get_jwks_decoded

settings = get_settings_singleton()
_log = logging.getLogger("app.http")

RLS_URL = (
    (settings.TOO_SB_DB_RLS or "").strip()
    or (settings.TOO_SB_RLS or "").strip()
    or settings.TOO_SB_DB
)

async_engine_rls = create_async_engine(RLS_URL,pool_pre_ping=True,echo=False,)
AsyncSessionLocal_RLS = async_sessionmaker(async_engine_rls,expire_on_commit=False,)
RLS_ROLE = (settings.TOO_SB_RLS_ROLE or "").strip()
_ROLE_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


async def get_db_rls(decoded: dict = Depends(get_jwks_decoded),) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal_RLS() as session:
        async with session.begin():
            claims_for_rls = dict(decoded)
            if not claims_for_rls.get("sba_ten_id"):
                app_metadata = claims_for_rls.get("app_metadata")
                user_metadata = claims_for_rls.get("user_metadata")
                app_ten_id = app_metadata.get("sba_ten_id") if isinstance(app_metadata, dict) else None
                user_ten_id = user_metadata.get("sba_ten_id") if isinstance(user_metadata, dict) else None
                fallback_ten_id = app_ten_id or user_ten_id
                if fallback_ten_id:
                    claims_for_rls["sba_ten_id"] = fallback_ten_id
                    _log.info(
                        "RLS claims normalized: sba_ten_id source=%s value=%s",
                        "app_metadata"
                        if app_ten_id
                        else "user_metadata"
                        if user_ten_id
                        else "unknown",
                        fallback_ten_id,
                    )
                else:
                    raise RuntimeError(
                        "RLS requires tenant claim 'sba_ten_id' (top-level or in app_metadata/user_metadata)."
                    )

            claims_json = json.dumps(claims_for_rls)
            await session.execute(
                text("select set_config('request.jwt.claims', :claims, true)"),
                {"claims": claims_json},
            )
            _log.info(
                "RLS claims set: sub=%s sba_ten_id=%s",
                claims_for_rls.get("sub"),
                claims_for_rls.get("sba_ten_id"),
            )
            if RLS_ROLE:
                if not _ROLE_NAME_PATTERN.fullmatch(RLS_ROLE):
                    raise RuntimeError(
                        f"Invalid TOO_SB_RLS_ROLE={RLS_ROLE!r}. Use a simple postgres identifier, e.g. authenticated."
                    )
                try:
                    await session.execute(text(f'SET LOCAL ROLE "{RLS_ROLE}"'))
                except SQLAlchemyProgrammingError as exc:
                    raise RuntimeError(
                        "Failed to switch DB role for RLS. "
                        f"Current connection user is missing membership in role '{RLS_ROLE}'. "
                        f"Run in SQL as admin: GRANT {RLS_ROLE} TO <your_connection_user>;"
                    ) from exc
            role_check = await session.execute(
                text(
                    "select current_user::text as current_user, "
                    "session_user::text as session_user, "
                    "current_setting('role', true)::text as active_role, "
                    "auth.jwt() ->> 'sba_ten_id' as jwt_ten_id"
                )
            )
            role_row = role_check.mappings().one()
            _log.info(
                "RLS db context: current_user=%s session_user=%s active_role=%s jwt_ten_id=%s",
                role_row["current_user"],
                role_row["session_user"],
                role_row["active_role"],
                role_row["jwt_ten_id"],
            )
            yield session
