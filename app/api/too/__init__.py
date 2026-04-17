from fastapi import APIRouter

from .r1_new_user_provision import newUserRou
from .r2_dashboard import homeRou
from .s1_me import userProfileRou
from .s2_be import beRou
from .s3_client import clientRou

rouToo = APIRouter()

rouToo.include_router(newUserRou)
rouToo.include_router(homeRou)
rouToo.include_router(userProfileRou)
rouToo.include_router(beRou)
rouToo.include_router(clientRou)
