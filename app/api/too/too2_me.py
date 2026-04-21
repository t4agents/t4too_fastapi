import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_async import get_db_admin
from app.db.models.too.z_user import ZUserDB
from app.schemas.sch_userprofile import UserProfileOut, UserProfileUpdate
from app.service.ser_userprofile import fetch_user_profile, update_user_profile

_log = logging.getLogger(__name__)
    
meRou = APIRouter()


def _to_out(user: ZUserDB) -> UserProfileOut:
    return UserProfileOut(
        email=user.email,
        display_name=user.display_name,
        position=user.position,
        country=user.country,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        plan_type=user.plan_type,
        avatar=user.avatar,
        state=user.state,
        zip=user.zip,
        tax_no=user.tax_no,
        note=user.note,
    )


@meRou.get("/getme", response_model=UserProfileOut)
async def get_user_profile2(
    zjwt: dict = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_admin),
):
    user = await fetch_user_profile(zjwt, db)
    return _to_out(user)


@meRou.post("/saveme", response_model=UserProfileOut)
async def post_user_profile2(
    payload: UserProfileUpdate,
    zjwt: dict = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_admin),
):
    updates = payload.model_dump(exclude_unset=True)
    user = await update_user_profile(zjwt, db, updates)
    return _to_out(user)
