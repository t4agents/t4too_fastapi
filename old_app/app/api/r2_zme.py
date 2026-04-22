from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.db_async import get_session
from app.schemas import sch_user, sch_be
from app.service import  ser2_zme, ser3_be

from app.core.dependency_injection import ZMeDataClass, get_zme

zmeRou = APIRouter()

class ChangeActiveBid(BaseModel): rzbid: UUID

@zmeRou.get("/get_me")
async def getMe(zme: ZMeDataClass = Depends(get_zme),):
    return await ser2_zme.get_me(zme)   # zuid, ztid, zbid


@zmeRou.get("/get_myorg")
async def getmyorg(zme: ZMeDataClass = Depends(get_zme),):
    return await ser2_zme.get_myorg(zme)   



@zmeRou.patch("/patch_me", response_model=sch_user.MyUserResponse)
async def patchme(data: sch_user.MyUserUpdate,zme: ZMeDataClass = Depends(get_zme),):
    print(f"Received patch request for user with data: {data} and scope: {zme}")
    return await ser2_zme.patch_me(zme, data)
    

@zmeRou.patch("/patch_myorg", response_model=sch_be.BizEntityResponse)
async def patchmyorg(data: sch_be.BizEntityUpdate,zme: ZMeDataClass = Depends(get_zme),):
    print(f"Received patch request for user with data: {data} and scope: {zme}")
    return await ser2_zme.patch_myorg(zme, data)



@zmeRou.patch("/change_active_bid")
async def patch_zbid(    payload: ChangeActiveBid,     zme: ZMeDataClass = Depends(get_zme),):
    return await ser3_be.patch_active_bid(payload.rzbid, zme)
