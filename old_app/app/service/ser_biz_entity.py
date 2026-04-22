from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.m_biz_entity import BizEntity
from app.schemas.sch_biz_entity import BizEntityCreate, BizEntityUpdate


async def create_biz_entity(data: BizEntityCreate, db: AsyncSession) -> BizEntity:
    """Create a new business entity."""
    entity = BizEntity(**data.model_dump())
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


async def get_biz_entity(entity_id: UUID, db: AsyncSession) -> BizEntity:
    """Get business entity by ID."""
    result = await db.execute(
        select(BizEntity).where(BizEntity.id == entity_id, BizEntity.is_deleted != True)
    )
    entity = result.scalars().first()

    if not entity:
        raise HTTPException(status_code=404, detail="Business entity not found")

    return entity


async def list_biz_entities(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[BizEntity]:
    """List all business entities with pagination."""
    result = await db.execute(
        select(BizEntity).where(BizEntity.is_deleted != True).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def update_biz_entity(
    entity_id: UUID, data: BizEntityUpdate, db: AsyncSession
) -> BizEntity:
    """Update an existing business entity."""
    entity = await get_biz_entity(entity_id, db)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return entity


async def delete_biz_entity(entity_id: UUID, db: AsyncSession) -> dict:
    """Delete a business entity by ID."""
    entity = await get_biz_entity(entity_id, db)
    entity.is_deleted = True
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    return {"detail": "Business entity soft-deleted successfully"}


async def get_entity_by_name(name: str, db: AsyncSession) -> Optional[BizEntity]:
    """Get business entity by name."""
    result = await db.execute(
        select(BizEntity).where(BizEntity.name == name, BizEntity.is_deleted != True)
    )
    return result.scalars().first()


async def get_entity_by_business_number(business_number: str, db: AsyncSession) -> Optional[BizEntity]:
    """Get business entity by CRA Business Number."""
    result = await db.execute(
        select(BizEntity).where(BizEntity.business_number == business_number, BizEntity.is_deleted != True)
    )
    return result.scalars().first()


async def get_entity_count(db: AsyncSession) -> int:
    """Get total number of business entities."""
    result = await db.execute(select(BizEntity).where(BizEntity.is_deleted != True))
    return len(result.scalars().all())
