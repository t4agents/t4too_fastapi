from uuid import UUID, uuid4

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency_injection import ZMeDataClass
from app.db.models import m_be, m_user, m_user_client, m_zme 
from app.schemas import sch_be, sch_user
# from app.service.ser_be import get_biz_entity_by_id


async def get_me(zme: ZMeDataClass) -> m_user.UserDB:
    result = await zme.zdb.execute(select(m_user.UserDB).where(m_user.UserDB.id == zme.zuid))
    me = result.scalars().first()
    print(f"Queried user with zid {zme.zuid}: {me}")
    if not me:raise HTTPException(status_code=404, detail="User not found")
    return me


async def patch_me(zme: ZMeDataClass, data: sch_user.MyUserUpdate) -> m_user.UserDB:
    print(f"Attempting to update user with UID: {zme.zuid}")
    
    user = await get_me(zme)
    print(f"Updating user {zme.zuid} with data: {data} and current user data: {user}")

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    zme.zdb.add(user)
    await zme.zdb.flush()
    await zme.zdb.refresh(user)
    return user



async def get_myorg(zme: ZMeDataClass) -> m_be.BizEntity:
    """Get business entity by ID."""
    result = await zme.zdb.execute(select(m_be.BizEntity).where(m_be.BizEntity.owner_id == zme.zuid))
    entity = result.scalars().first()
    if not entity:raise HTTPException(status_code=404, detail="Business entity not found")
    return entity


async def patch_myorg(zme: ZMeDataClass, data: sch_be.BizEntityUpdate) -> m_be.BizEntity:
    """Update an existing business entity."""
    entity = await get_myorg(zme)

    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entity, field, value)

    zme.zdb.add(entity)
    await zme.zdb.flush()
    await zme.zdb.refresh(entity)
    return entity
