from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.db_async import get_db
from app.schemas.sch_biz_entity import BizEntityCreate, BizEntityUpdate, BizEntityResponse
from app.service.ser_biz_entity import (
    create_biz_entity,
    get_biz_entity,
    list_biz_entities,
    update_biz_entity,
    delete_biz_entity,
    get_entity_by_name,
    get_entity_by_business_number,
    get_entity_count,
)

bizEntityRou = APIRouter()


@bizEntityRou.post("", response_model=BizEntityResponse)
async def create(
    data: BizEntityCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new business entity."""
    return await create_biz_entity(data, db)


@bizEntityRou.get("/{entity_id}", response_model=BizEntityResponse)
async def get(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get business entity by ID."""
    return await get_biz_entity(entity_id, db)


@bizEntityRou.get("", response_model=List[BizEntityResponse])
async def list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List all business entities with pagination."""
    return await list_biz_entities(db, skip=skip, limit=limit)


@bizEntityRou.get("/search/by-name", response_model=BizEntityResponse)
async def search_by_name(
    name: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search business entity by name."""
    entity = await get_entity_by_name(name, db)
    if not entity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Business entity not found")
    return entity


@bizEntityRou.get("/search/by-business-number", response_model=BizEntityResponse)
async def search_by_business_number(
    business_number: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search business entity by CRA Business Number."""
    entity = await get_entity_by_business_number(business_number, db)
    if not entity:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Business entity not found")
    return entity


@bizEntityRou.put("/{entity_id}", response_model=BizEntityResponse)
async def update(
    entity_id: UUID,
    data: BizEntityUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a business entity."""
    return await update_biz_entity(entity_id, data, db)


@bizEntityRou.delete("/{entity_id}")
async def delete(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a business entity."""
    return await delete_biz_entity(entity_id, db)


@bizEntityRou.get("/stats/count")
async def get_count(
    db: AsyncSession = Depends(get_db),
):
    """Get total number of business entities."""
    count = await get_entity_count(db)
    return {"total": count}
