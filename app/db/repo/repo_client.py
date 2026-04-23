from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.too.z_client import ZClientDB
from app.db.repo.repo_utils import coerce_model_values
from app.schemas.sch_ai import JWType


async def list_clients(db: AsyncSession, zjwt: JWType) -> List[ZClientDB]:
    result = await db.execute(
        select(ZClientDB)
        .order_by(ZClientDB.created_at.desc())
    )
    return list(result.scalars().all())


async def get_client_by_id(db: AsyncSession, client_id: UUID, zjwt: JWType) -> Optional[ZClientDB]:
    result = await db.execute(
        select(ZClientDB).where(ZClientDB.id == client_id, ZClientDB.created_by == zjwt.zuid)
    )
    return result.scalar_one_or_none()


async def create_client(db: AsyncSession, payload: dict) -> ZClientDB:
    client = ZClientDB(**coerce_model_values(ZClientDB, payload))
    db.add(client)
    await db.commit()
    # await db.refresh(client)
    return client


async def update_client_fields(db: AsyncSession, client: ZClientDB, updates: dict) -> ZClientDB:
    if updates:
        for key, value in coerce_model_values(client, updates).items():
            setattr(client, key, value)
        db.add(client)
        await db.commit()
        # await db.refresh(client)
    return client
