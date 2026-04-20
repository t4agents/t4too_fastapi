# db.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine

from app.config import get_settings_singleton
settings = get_settings_singleton()

TOO_URL = settings.TOO_SB_DB


too_async_engine = create_async_engine(TOO_URL,    pool_pre_ping=True,    echo=False, )
TooDbSession = async_sessionmaker(too_async_engine,    expire_on_commit=False,)


async def get_session():
    async with TooDbSession() as t4_session:
        async with t4_session.begin():
            yield t4_session



async_engine_admin = create_async_engine(
    TOO_URL,
    pool_pre_ping=True,
    echo=False,  # True only in local dev
)

AsyncSessionLocal_Admin = async_sessionmaker(
    async_engine_admin,
    expire_on_commit=False,
)

async def get_db_rls() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal_Admin() as session:
        yield session
