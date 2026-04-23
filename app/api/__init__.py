from fastapi import APIRouter

from .too import rouToo
from .t4 import rouT4
from .inv import invRou
from .ai import rouAI
from .bi import rouBI

rou = APIRouter()

rou.include_router(rouAI,  tags=["ai"])

rou.include_router(invRou, prefix="/inv" )
rou.include_router(rouToo, prefix="/too", tags=["too"])
rou.include_router(rouT4, prefix="/t4", tags=["t4"])
rou.include_router(rouBI, prefix="/bi", tags=["bi"])
