from typing import List, Optional
from uuid import UUID, uuid4
from firebase_admin import db
from psycopg2 import IntegrityError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.core.dependency_injection import ZBeList_DataClass, ZMeDataClass
from app.db.models import m_zme, m_be, m_user_client
from app.schemas import sch_be
from app.schemas.sch_be import BizEntityCreate, BizEntityUpdate


from app.db.models.m_zme import ZMeDB
from app.db.seeds.seed_payroll_schedules import ensure_payroll_schedules_for_be


async def patch_active_bid(rzbid: UUID,  zme: ZMeDataClass,) -> dict[str, str | None]:

    print(f"patch_active_bid called with zbid: {rzbid} and zme: {zme}")
    stmt = update(ZMeDB).where(ZMeDB.id == zme.zuid).values(biz_id=rzbid)
    await zme.zdb.execute(stmt)
    await zme.zdb.flush()
    
    return {"message": "active_bid updated",}
    


async def new_be(payload: BizEntityCreate, zme: ZMeDataClass) -> m_be.BizEntity:
    """Create a new business entity."""
    generated_biz_id = uuid4()

    entity_payload = payload.model_dump(exclude_none=True)
    for immutable_key in ("id", "biz_id", "ten_id", "owner_id"):entity_payload.pop(immutable_key, None)

    entity = m_be.BizEntity(
        id      =generated_biz_id,
        biz_id  =generated_biz_id,
        ten_id  =zme.ztid,
        owner_id=zme.zuid,
        **entity_payload,
    )
    if zme.zdb is None:raise HTTPException(status_code=500, detail="Database session not available in user context")   
    zme.zdb.add(entity)

    user_client = m_user_client.UserClient(
        user_id =zme.zuid,
        biz_id  =generated_biz_id,
        ten_id  =zme.ztid,
    )
    zme.zdb.add(user_client)

    await ensure_payroll_schedules_for_be(
        zme.zdb,
        ten_id=zme.ztid,
        biz_id=generated_biz_id,
        owner_id=zme.zuid,
        created_by=zme.zuid,
    )

    await zme.zdb.flush()  # Flush to assign IDs and ensure data is in the session
    await zme.zdb.refresh(entity)
    return entity


async def edit_be(zme: ZMeDataClass, payload: sch_be.BizEntityUpdate) -> m_be.BizEntity:
    result = await zme.zdb.execute(select(m_be.BizEntity).where(m_be.BizEntity.id == payload.id))
    entity = result.scalars().first()
    if not entity:raise HTTPException(status_code=404, detail="Business entity not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items(): setattr(entity, field, value)

    zme.zdb.add(entity)
    await zme.zdb.flush()
    await zme.zdb.refresh(entity)
    return entity


