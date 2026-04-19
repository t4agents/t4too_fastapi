import json
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings_singleton
from app.core.auth import get_jwks_decoded

settings = get_settings_singleton()

RLS_URL = (settings.TOO_SB_DB_RLS or "").strip() or settings.TOO_SB_DB

async_engine_rls = create_async_engine(
    RLS_URL,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal_RLS = async_sessionmaker(
    async_engine_rls,
    expire_on_commit=False,
)


async def get_db_rls(
    decoded: dict = Depends(get_jwks_decoded),
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal_RLS() as session:
        async with session.begin():
            claims_json = json.dumps(decoded)
            await session.execute(
                text("select set_config('request.jwt.claims', :claims, true)"),
                {"claims": claims_json},
            )
            await session.execute(text("set local role authenticated"))
            yield session
