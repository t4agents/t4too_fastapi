from fastapi import APIRouter

from .t4_employee import employeeRou
from .t4_entry import entryRou
from .t4_history import historyRou
from .t4_period import periodRou
from .t4_schedule import scheduleRou

rouT4 = APIRouter()

rouT4.include_router(employeeRou)
rouT4.include_router(entryRou)
rouT4.include_router(historyRou)
rouT4.include_router(periodRou)
rouT4.include_router(scheduleRou)
