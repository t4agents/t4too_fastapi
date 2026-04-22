from __future__ import annotations

import re
from calendar import monthrange
from datetime import date, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_period import PayrollPeriodDB
from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.db.repo.repo_payroll_period import list_payroll_periods
from app.service.ser_payroll_common import period_key_from_dates


async def fetch_payroll_periods(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollPeriodDB]:
    return await list_payroll_periods(db, sbu_client_id)


async def get_or_create_period_for_window(
    db: AsyncSession,
    schedule: PayrollScheduleDB,
    period_start: date,
    period_end: date,
    sbu_client_id: UUID,
) -> PayrollPeriodDB:
    if period_start is None or period_end is None:
        raise HTTPException(status_code=400, detail="Payroll period window is missing")

    period_key = period_key_from_dates(schedule.frequency, period_start, period_end)
    result = await db.execute(
        select(PayrollPeriodDB).where(
            PayrollPeriodDB.cli_id == sbu_client_id,
            PayrollPeriodDB.period_key == period_key,
        )
    )
    period = result.scalar_one_or_none()
    if period:
        return period

    max_period_number_result = await db.execute(
        select(func.max(PayrollPeriodDB.period_number)).where(
            PayrollPeriodDB.cli_id == sbu_client_id,
            PayrollPeriodDB.payroll_schedule_id == schedule.id,
        )
    )
    max_period_number = max_period_number_result.scalar_one_or_none() or 0

    period = PayrollPeriodDB(
        payroll_schedule_id=schedule.id,
        start_date=period_start,
        end_date=period_end,
        pay_date=_pay_date_from_period(schedule, period_end),
        period_key=period_key,
        period_number=max_period_number + 1,
        status="open",
        cli_id=sbu_client_id,
        biz_id=sbu_client_id,
        ten_id=_to_uuid_or_none((schedule.ten_id or schedule.cli_id)),
        usr_id=schedule.usr_id,
        created_by=schedule.created_by,
    )
    db.add(period)
    await db.flush()
    await db.refresh(period)
    return period


def _to_uuid_or_none(value: UUID | str | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError:
        return None


def _pay_date_from_period(schedule: PayrollScheduleDB, period_end: date | None) -> date | None:
    if period_end is None:
        return None

    payon_raw = (schedule.payon or "").strip()
    if not payon_raw:
        return period_end

    payon = payon_raw.lower()
    if payon in {"eom", "end of month", "last day of month", "month end"}:
        last_day = monthrange(period_end.year, period_end.month)[1]
        return date(period_end.year, period_end.month, last_day)

    match = re.search(r"\d+", payon)
    if match:
        day = int(match.group())
        if day <= 0:
            return period_end
        last_day = monthrange(period_end.year, period_end.month)[1]
        candidate = date(period_end.year, period_end.month, min(day, last_day))
        if candidate < period_end:
            next_year, next_month = _next_month(period_end.year, period_end.month)
            next_last_day = monthrange(next_year, next_month)[1]
            candidate = date(next_year, next_month, min(day, next_last_day))
        return candidate

    weekday_map = {
        "monday": 0,
        "mon": 0,
        "tuesday": 1,
        "tue": 1,
        "tues": 1,
        "wednesday": 2,
        "wed": 2,
        "thursday": 3,
        "thu": 3,
        "thur": 3,
        "thurs": 3,
        "friday": 4,
        "fri": 4,
        "saturday": 5,
        "sat": 5,
        "sunday": 6,
        "sun": 6,
    }
    if payon in weekday_map:
        target = weekday_map[payon]
        days_ahead = (target - period_end.weekday()) % 7
        return period_end + timedelta(days=days_ahead)

    return period_end


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1
