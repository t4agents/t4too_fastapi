from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.dependency_injection import ZBeList_DataClass, ZMeDataClass, get_zme_be_list, get_zme
from app.schemas import sch_be
from app.schemas.sch1_zme import ZBeList
from app.schemas.sch_be import BizEntityCreate, BizEntityUpdate, BizEntityResponse
from app.service import ser2_zme
from app.service import ser3_be
from app.service.ser3_be import new_be

beRou = APIRouter()


@beRou.get("/list", response_model=ZBeList)
async def list(zbe_list: ZBeList = Depends(get_zme_be_list)):
    return zbe_list


@beRou.post("/new", response_model=BizEntityResponse)
async def create(payload: BizEntityCreate,zme: ZMeDataClass = Depends(get_zme),):
    return await new_be(payload, zme)


@beRou.patch("/edit", response_model=sch_be.BizEntityResponse)
async def patchmyorg(payload: sch_be.BizEntityUpdate,zme: ZMeDataClass = Depends(get_zme),):
    print(f"Received patch request for user with data: {payload} and scope: {zme}")
    return await ser3_be.edit_be(zme, payload)




# @beRou.get("/stats/count")
# async def get_count(
#     db: AsyncSession = Depends(get_session),
# ):
#     """Get total number of business entities."""
#     count = await get_entity_count(db)
#     return {"total": count}



# @beRou.get("/getbyid", response_model=BizEntityResponse)
# async def get(
#     zme: ZMeDataClass = Depends(get_zme),
#     db: AsyncSession = Depends(get_session),
# ):
#     return await get_be_profile(zme.ztid, db)





# @beRou.patch("/patchbyid/{be_id}", response_model=BizEntityResponse)
# async def patch(
#     be_id: UUID,
#     data: BizEntityUpdate,
#     _zme: ZMeDataClass = Depends(get_zme),
#     db: AsyncSession = Depends(get_session),
# ):
#     """Patch update a business entity with user context."""
#     return await update_biz_entity_by_id(be_id, data, db)


# @beRou.delete("/deletebyid/{be_id}")
# async def delete(
#     be_id: UUID,
#     db: AsyncSession = Depends(get_session),
# ):
#     """Delete a business entity."""
#     return await delete_biz_entity_by_id(be_id, db)
