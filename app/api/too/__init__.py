from fastapi import APIRouter

from .too1_new_user_provision import newUserRou
from .too2_me import userProfileRou
from .too3_be import beRou
from .too4_client import clientRou

rouToo = APIRouter()

rouToo.include_router(newUserRou)
rouToo.include_router(userProfileRou)
rouToo.include_router(beRou)
rouToo.include_router(clientRou)
