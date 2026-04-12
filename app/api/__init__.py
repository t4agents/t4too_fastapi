from fastapi import APIRouter

from app.api.r1_new_user_provision import newUserRou

rou = APIRouter()
rou.include_router(newUserRou)
