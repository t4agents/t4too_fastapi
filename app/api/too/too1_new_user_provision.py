import logging

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_jwks_decoded
from app.db.conn.db_async import get_db_admin
from app.service.ser1_new_user import provision_new_user, provision_new_user_with_seed
from app.schemas.sch_ai import JWType
from app.core.auth import get_zjwt

newUserRou = APIRouter()
_log = logging.getLogger(__name__)


@newUserRou.post("/r1_new_user_provision", response_class=PlainTextResponse)
async def post_profile(
    decoded: dict = Depends(get_jwks_decoded),
    db: AsyncSession = Depends(get_db_admin),
):
    try:
        await provision_new_user(decoded, db)
    except Exception:raise
    return "success"


# @newUserRou.post("/r1_new_user_provision_with_seed", response_class=PlainTextResponse)
# async def post_profile2(
#     decoded: dict = Depends(get_jwks_decoded),
#     db: AsyncSession = Depends(get_db_admin),
# ):
#     try:
#         await provision_new_user_with_seed(decoded, db)
#     except Exception:raise
#     return "success"

@newUserRou.post("/newprovision_seed", response_class=PlainTextResponse)
async def post_profile_zjwt(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_admin),
):
    try:
        await provision_new_user_with_seed(zjwt, db)
    except Exception:raise
    return "success"

