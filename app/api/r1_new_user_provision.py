from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_jwks_decoded
from app.db.conn.db_async import get_db_admin
from app.service.ser1_new_user import provision_new_user

newUserRou = APIRouter()


@newUserRou.post("/r1_new_user_provision", response_class=PlainTextResponse)
async def post_profile(
    decoded: dict = Depends(get_jwks_decoded),
    db: AsyncSession = Depends(get_db_admin),
):
    await provision_new_user(decoded, db)
    return "success"


