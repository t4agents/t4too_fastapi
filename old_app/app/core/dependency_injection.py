from typing import Sequence
from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_async import get_session
from app.db.models import m_be, m_user, m_user_client, m_zme
from app.schemas.sch_be import BizEntityBase

from .firebase_auth import core_verify_firebase_token

security = HTTPBearer()

@dataclass(frozen=True)
class ZMeDataClass:
    ztid: UUID
    zuid: UUID
    zbid: UUID
    zdb: AsyncSession 

@dataclass(frozen=True)
class ZBeList_DataClass(ZMeDataClass):
    zbe_list: Sequence[dict] = ()


# wrap the above function with FastAPI dependency to extract user context from database
async def get_zme(credentials: HTTPAuthorizationCredentials = Depends(security),session: AsyncSession = Depends(get_session),) -> ZMeDataClass:
    decoded = core_verify_firebase_token(credentials.credentials)
    fb_uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
    if not fb_uid:raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    stmt = select(m_zme.ZMeDB).where(m_zme.ZMeDB.firebase_uid == str(fb_uid))
    result = await session.execute(stmt)
    me = result.scalar_one_or_none()

    if not me:raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not me.id:raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no tenant")
    if not me.biz_id:raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User has no active business")

    # Set tenant context for this DB session so RLS policies can evaluate ten_id.
    ten_id = str(me.ten_id)
    await session.execute(text("select set_config('t4rls.tid', :ten_id, true)"), {"ten_id": ten_id})

    return ZMeDataClass(
        ztid=me.ten_id,
        zuid=me.id,
        zbid=me.biz_id,
        zdb=session,
    )



async def get_zme_be_list(zme: ZMeDataClass = Depends(get_zme),) -> ZBeList_DataClass:
    result = await zme.zdb.execute(select(m_user_client.UserClient.biz_id).where(m_user_client.UserClient.user_id == zme.zuid))
    linked_clients = list(result.scalars().all())
    print(f"Linked clients for user {zme.zuid}: {linked_clients}")

    clients = await zme.zdb.execute(select(m_be.BizEntity).where(m_be.BizEntity.id.in_(linked_clients)))
    clientListOCR=clients.scalars().all()
    
    clientList = [BizEntityBase.model_validate(e).model_dump() for e in clientListOCR]

    return ZBeList_DataClass(
        ztid=zme.ztid,
        zuid=zme.zuid,
        zbid=zme.zbid,
        zdb =zme.zdb,
        zbe_list=clientList,
    )
