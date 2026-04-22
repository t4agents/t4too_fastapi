# db.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine

from app.config import get_settings_singleton
settings = get_settings_singleton()

T4_URL = settings.T4_ASYNC
ADMIN_URL = settings.T4_ADMIN

t4_db_async_engine = create_async_engine(T4_URL,    pool_pre_ping=True,    echo=False, )
T4DbSession = async_sessionmaker(t4_db_async_engine,    expire_on_commit=False,)


async def get_session():
    async with T4DbSession() as t4_session:
        async with t4_session.begin():
            yield t4_session



async_engine_admin = create_async_engine(
    ADMIN_URL,
    pool_pre_ping=True,
    echo=False,  # True only in local dev
)

AsyncSessionLocal_Admin = async_sessionmaker(
    async_engine_admin,
    expire_on_commit=False,
)

async def get_db_admin() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal_Admin() as session:
        yield session
