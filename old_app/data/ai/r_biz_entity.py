from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.firebase_auth import ZMe_DataClass, ZMe_DataClass, get_zme, get_zme
from app.db.db_async import get_session
from app.schemas.sch_be import BizEntityCreate, BizEntityUpdate, BizEntityResponse
from app.service.ser3_be import (
    new_be,
    list_be,
    get_entity_count,
    get_be_profile,
    update_biz_entity_by_id,
)

beRou = APIRouter()


@beRou.post("/postnew", response_model=BizEntityResponse)
async def create(
    data: BizEntityCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create a new business entity."""
    return await new_be(data, db)


@beRou.get("/stats/count")
async def get_count(
    db: AsyncSession = Depends(get_session),
):
    """Get total number of business entities."""
    count = await get_entity_count(db)
    return {"total": count}


@beRou.get("/getlist", response_model=List[BizEntityResponse])
async def list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    myscope: ZMe_DataClass = Depends(get_zme),
):
    """List all business entities with pagination."""
    return await list_be(
        myscope._session,
        tenant_id=myscope.ztid,
        client_ids=myscope.client_ids,
        skip=skip,
        limit=limit,
    )


@beRou.get("/getbyid", response_model=BizEntityResponse)
async def get(
    myscope: ZMe_DataClass = Depends(get_zme),
    db: AsyncSession = Depends(get_session),
):
    return await get_be_profile(myscope.ztid, db)





@beRou.patch("/patchbyid", response_model=BizEntityResponse)
async def patch(
    data: BizEntityUpdate,
    myscope: ZMe_DataClass = Depends(get_zme),
    db: AsyncSession = Depends(get_session),
):
    """Patch update a business entity with user context."""
    # User context available:
    # context.uid - database user ID
    # context.tid - tenant ID
    entity = await get_be_profile(myscope.ztid, db)
    return await update_biz_entity_by_id(entity.id, data, db)


# @beRou.delete("/{entity_id}")
# async def delete(
#     entity_id: UUID,
#     context: Dict[str, Any] = Depends(get_my_scope),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Delete a business entity."""
#     tenant_id = _tenant_id_from_context(context)
#     return await delete_biz_entity_by_id(tenant_id, entity_id, db)
