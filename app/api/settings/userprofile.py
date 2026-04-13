from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.too.z_user import ZUserDB
from app.schemas.sch_userprofile import UserProfileOut, UserProfileUpdate
from app.service.ser_userprofile import fetch_user_profile, update_user_profile

userProfileRou = APIRouter(prefix="/settings")


def _to_out(user: ZUserDB) -> UserProfileOut:
    return UserProfileOut(
        email=user.email,
        display_name=user.display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        plan_type=user.plan_type,
        avatar=user.avatar,
    )


@userProfileRou.get("/userprofile", response_model=UserProfileOut)
async def get_user_profile(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    user = await fetch_user_profile(zuid, db)
    return _to_out(user)


@userProfileRou.post("/userprofile", response_model=UserProfileOut)
async def post_user_profile(
    payload: UserProfileUpdate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    updates = payload.model_dump(exclude_unset=True)
    user = await update_user_profile(zuid, db, updates)
    return _to_out(user)
