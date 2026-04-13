from fastapi import APIRouter

from app.api.r1_new_user_provision import newUserRou
from app.api.settings.userprofile import userProfileRou

rou = APIRouter()
rou.include_router(newUserRou)
rou.include_router(userProfileRou)
