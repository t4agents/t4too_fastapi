from fastapi import APIRouter
from .inv2_invoices import inv2Rou 
from .inv1_home import homeRou

from .settings import settingsRou

invRou = APIRouter()

invRou.include_router(homeRou, tags=["i_home"])
invRou.include_router(inv2Rou, tags=["i_nvoices"])
invRou.include_router(settingsRou, prefix="/settings", tags=["i_settings"])

