from fastapi import APIRouter

from .t4_employee import employeeRou

rouT4 = APIRouter()

rouT4.include_router(employeeRou)
