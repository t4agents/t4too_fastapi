from fastapi import APIRouter
from .inv2_invoices import invMainRou 
from .inv1_home import homeRou

from .settings import settingsRou

invRou = APIRouter()

invRou.include_router(homeRou, tags=["i_home"])
invRou.include_router(invMainRou, tags=["i_nvoices"])
invRou.include_router(settingsRou, prefix="/settings", tags=["i_settings"])

