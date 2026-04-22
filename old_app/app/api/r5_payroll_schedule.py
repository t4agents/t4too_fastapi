from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import List

from app.core.dependency_injection import ZMeDataClass, get_zme
from app.schemas.sch_payroll_schedule import ScheduleBase
from app.service.ser5_payroll_schedule import (list_schedules, edit_schedule)

scheduleRow = APIRouter()


@scheduleRow.get("/list",response_model=List[ScheduleBase])
async def list_payroll_schedules(
    skip: int = Query(0, ge=0, description="Number of schedules to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum schedules to return"),
    zme: ZMeDataClass = Depends(get_zme),
):
    return await list_schedules(zme, skip=skip, limit=limit)




@scheduleRow.post("/edit",response_model=ScheduleBase)
async def update_payroll_schedule(
    payload: ScheduleBase,
    zme: ZMeDataClass = Depends(get_zme),
):
    return await edit_schedule(payload, zme)



