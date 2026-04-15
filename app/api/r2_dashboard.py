from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.too.z_be import ZBizEntityDB
from app.db.models.too.z_user import ZUserDB
from app.schemas.sch_homeinfo import HomeBizOut, HomeInfoOut
from app.schemas.sch_userprofile import UserProfileOut
from app.service.ser_dashboard import fetch_homeinfo

homeRou = APIRouter(prefix="/home")


def _to_out(user: ZUserDB, be: ZBizEntityDB | None) -> HomeInfoOut:
    return HomeInfoOut(
        user=UserProfileOut(
            email=user.email,
            display_name=user.display_name,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            plan_type=user.plan_type,
            avatar=user.avatar,
        ),
        biz=HomeBizOut(
            be_name=be.be_name if be else None,
        ),
    )


@homeRou.get("/dashboard", response_model=HomeInfoOut)
async def get_user_profile(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    user, be = await fetch_homeinfo(zuid, db)
    return _to_out(user, be)
