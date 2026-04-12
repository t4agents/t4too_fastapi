from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_async import get_db_admin
from app.core.firebase_auth import get_firebase_decoded
from app.service.ser1_new_user import new_user

newUserRou = APIRouter()

@newUserRou.post("/new_user")
async def post_profile(
    decoded: dict = Depends(get_firebase_decoded),
    db: AsyncSession = Depends(get_db_admin),
):
    return await new_user(decoded, db)


