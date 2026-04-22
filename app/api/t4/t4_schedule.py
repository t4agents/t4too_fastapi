from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.schemas.sch_payroll_schedule import PayrollScheduleOut
from app.service.ser_payroll_schedule import fetch_payroll_schedules

scheduleRou = APIRouter()


def _to_db_dict(payroll_schedule: PayrollScheduleDB) -> dict[str, Any]:
    return {
        column.name: getattr(payroll_schedule, column.name)
        for column in payroll_schedule.__table__.columns
    }


@scheduleRou.get("/get_payroll_schedule_list", response_model=list[PayrollScheduleOut])
async def get_payroll_schedule_list(
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    sbu_client_id = zjwt["user_metadata"]["sbu_client_id"]
    schedules = await fetch_payroll_schedules(sbu_client_id, db)
    return [PayrollScheduleOut(**_to_db_dict(schedule)) for schedule in schedules]
