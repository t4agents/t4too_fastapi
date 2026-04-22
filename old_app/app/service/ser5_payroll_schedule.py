from calendar import monthrange
from datetime import date, timedelta
import re
from decimal import Decimal
from uuid import UUID
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_payroll_entry import PayrollEntry
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.db.models.m_employee import Employee
from app.db.repo.repo_payroll_entry import PayrollEntryRepository
from app.schemas.sch_payroll_schedule import ScheduleBase
from app.service.payroll_period import get_or_create_period_for_window
from app.util.payroll_calc_on_2026 import (
    calculate_payroll_deductions_on_2026,
    periods_per_year_from_frequency,
)
from app.util.payroll_period_key import period_key_from_dates


# ---- PAYROLL SCHEDULE OPERATIONS ----
async def list_schedules(zme: ZMeDataClass, skip: int = 0, limit: int = 100):
    result = await zme.zdb.execute(select(PayrollSchedule).where(PayrollSchedule.biz_id == zme.zbid).offset(skip).limit(limit))
    return result.scalars().all()




# ---- PAYROLL SCHEDULE OPERATIONS ----"""Update a payroll schedule."""
async def edit_schedule(payload: ScheduleBase, zme: ZMeDataClass):
    result = await zme.zdb.execute(
        select(PayrollSchedule).where(
            PayrollSchedule.id == payload.id,
            PayrollSchedule.biz_id == zme.zbid,
        )
    )
    schedule = result.scalars().first()
    
    if not schedule: raise HTTPException(status_code=404, detail=f"Payroll schedule with ID {payload.id} not found")     

    previous_status = (schedule.status or "").lower()
    incoming_status = (payload.status or "").lower()

    # Validate frequency
    
    # Validate effective dates
    
    # Update fields
    schedule.frequency = payload.frequency.lower()
    schedule.period = payload.period
    schedule.payon = payload.payon
    schedule.semi1 = payload.semi1
    schedule.semi2 = payload.semi2
    schedule.note = payload.note
    schedule.effective_from = payload.effective_from
    schedule.status = incoming_status

    if previous_status == "inactive" and incoming_status == "active":
        await _reset_entries_for_schedule(schedule, zme)
    else:
        await _recalculate_entries_for_schedule(schedule, zme)
    
    await zme.zdb.flush()
    await zme.zdb.refresh(schedule)
    
    return schedule


async def _recalculate_entries_for_schedule(schedule: PayrollSchedule, zme: ZMeDataClass) -> None:
    result = await zme.zdb.execute(
        select(PayrollEntry).where(
            PayrollEntry.schedule_id == schedule.id,
            PayrollEntry.biz_id == zme.zbid,
        )
    )
    entries = result.scalars().all()
    if not entries:
        return

    periods_per_year = _periods_per_year(schedule)

    for entry in entries:
        employment_type = (entry.employment_type or "other").lower()
        hourly_rate = entry.hourly_rate_snapshot or Decimal("0.00")
        regular_hours = entry.regular_hours or Decimal("0.00")
        overtime_hours = entry.overtime_hours or Decimal("0.00")
        adjustment = entry.adjustment or Decimal("0.00")

        if employment_type == "salary" and entry.annual_salary_snapshot is not None:
            base_gross = entry.annual_salary_snapshot / periods_per_year
            if overtime_hours > 0 and hourly_rate > 0:
                base_gross += overtime_hours * hourly_rate * Decimal("1.5")
        else:
            base_gross = (regular_hours * hourly_rate) + (overtime_hours * hourly_rate * Decimal("1.5"))

        gross = base_gross.quantize(Decimal("0.01"))

        deductions = calculate_payroll_deductions_on_2026(
            period_gross=base_gross,
            periods_per_year=periods_per_year,
            cpp_exempt=bool(entry.cpp_exempt_snapshot),
            ei_exempt=bool(entry.ei_exempt_snapshot),
            federal_basic_personal_amount=entry.federal_claim_snapshot,
            ontario_basic_personal_amount=entry.ontario_claim_snapshot,
        )

        entry.gross = gross
        entry.cpp = deductions["cpp"]
        entry.ei = deductions["ei"]
        entry.tax = deductions["tax"]
        entry.total_deduction = deductions["total_deduction"]
        entry.net = (gross - deductions["total_deduction"] + adjustment).quantize(Decimal("0.01"))


async def _reset_entries_for_schedule(schedule: PayrollSchedule, zme: ZMeDataClass) -> None:
    await zme.zdb.execute(delete(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid))

    period_start, period_end = _current_period_window(schedule)
    pay_date = _pay_date_from_period(schedule, period_end)
    await _create_entries_for_schedule(
        schedule,
        zme,
        period_start=period_start,
        period_end=period_end,
        pay_date=pay_date,
    )


async def _create_entries_for_schedule(
    schedule: PayrollSchedule,
    zme: ZMeDataClass,
    period_start: date | None = None,
    period_end: date | None = None,
    pay_date: date | None = None,
) -> None:
    employee_query = select(Employee).where(
        Employee.biz_id == zme.zbid,
        or_(Employee.is_deleted.is_(None), Employee.is_deleted.is_(False)),
    )
    employee_result = await zme.zdb.execute(employee_query)
    employees = employee_result.scalars().all()

    entries = []
    period = None
    period_key = None
    if period_start and period_end:
        period = await get_or_create_period_for_window(schedule, period_start, period_end, zme)
        period_key = period.period_key
        pay_date = period.pay_date
    if pay_date is None:
        pay_date = _pay_date_from_period(schedule, period_end)
    periods_per_year = _periods_per_year(schedule)
    for employee in employees:
        employment_type = (employee.employment_type or "other").lower()
        full_name = " ".join(part for part in [employee.first_name, employee.last_name] if part)
        gross = Decimal("0.00")
        if employment_type == "salary":
            if employee.annual_salary is not None:
                gross = (employee.annual_salary / periods_per_year).quantize(Decimal("0.01"))
        elif employment_type == "hourly":
            if employee.regular_hours is not None and employee.hourly_rate is not None:
                gross = (employee.regular_hours * employee.hourly_rate).quantize(Decimal("0.01"))
        deductions = calculate_payroll_deductions_on_2026(
            period_gross=gross,
            periods_per_year=periods_per_year,
            cpp_exempt=bool(employee.cpp_exempt),
            ei_exempt=bool(employee.ei_exempt),
            federal_basic_personal_amount=employee.federal_claim_amount,
            ontario_basic_personal_amount=employee.ontario_claim_amount,
        )
        entries.append(
            PayrollEntry(
                schedule_id=schedule.id,
                payroll_period_id=period.id if period else None,
                employee_id=employee.id,
                period_start=period_start,
                period_end=period_end,
                pay_date=pay_date,
                period_key=period_key,
                employment_type=employment_type,
                full_name=full_name,
                annual_salary_snapshot=employee.annual_salary,
                hourly_rate_snapshot=employee.hourly_rate,
                federal_claim_snapshot=employee.federal_claim_amount or Decimal("0.00"),
                ontario_claim_snapshot=employee.ontario_claim_amount or Decimal("0.00"),
                regular_hours=employee.regular_hours,
                overtime_hours=Decimal("0.00"),
                bonus=Decimal("0.00"),
                vacation=Decimal("0.00"),
                cpp=deductions["cpp"],
                ei=deductions["ei"],
                tax=deductions["tax"],
                gross=gross,
                total_deduction=deductions["total_deduction"],
                net=deductions["net"],
                cpp_exempt_snapshot=bool(employee.cpp_exempt),
                ei_exempt_snapshot=bool(employee.ei_exempt),
                biz_id=zme.zbid,
                ten_id=zme.ztid,
                owner_id=zme.zuid,
            )
        )

    if entries:
        zme.zdb.add_all(entries)
        await zme.zdb.flush()


def _periods_per_year(schedule: PayrollSchedule) -> int:
    return periods_per_year_from_frequency(schedule.frequency)


def _pay_date_from_period(schedule: PayrollSchedule, period_end: date | None) -> date | None:
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


def _current_period_window(schedule: PayrollSchedule) -> tuple[date | None, date | None]:
    freq = (schedule.frequency or "").lower()
    if freq not in {"weekly", "biweekly", "monthly", "semimonthly"}:
        return None, None

    effective = schedule.effective_from or date.today()
    if freq == "monthly":
        period_start = date(effective.year, effective.month, 1)
        period_end = date(effective.year, effective.month, monthrange(effective.year, effective.month)[1])
        return period_start, period_end

    if freq == "semimonthly":
        last_day = monthrange(effective.year, effective.month)[1]
        if effective.day <= 15:
            return date(effective.year, effective.month, 1), date(effective.year, effective.month, 15)
        return date(effective.year, effective.month, 16), date(effective.year, effective.month, last_day)

    if freq == "weekly":
        period_start = _monday_of_week(effective)
        period_end = period_start + timedelta(days=4)
        return period_start, period_end

    # biweekly: Monday to next Friday
    period_start = _monday_of_week(effective)
    period_end = period_start + timedelta(days=11)
    return period_start, period_end


def _period_end_from_start(freq: str, start: date, anchor_day: int) -> date:
    if freq == "weekly":
        return start + timedelta(days=6)
    if freq == "biweekly":
        return start + timedelta(days=13)
    if freq == "monthly":
        return _add_months(start, 1) - timedelta(days=1)
    if freq == "semimonthly":
        last_day = monthrange(start.year, start.month)[1]
        anchor_day = min(anchor_day, last_day)
        if start.day <= anchor_day:
            return date(start.year, start.month, anchor_day)
        return date(start.year, start.month, last_day)
    return start


def _add_months(value: date, months: int) -> date:
    month_index = (value.month - 1) + months
    year = value.year + (month_index // 12)
    month = (month_index % 12) + 1
    day = min(value.day, monthrange(year, month)[1])
    return date(year, month, day)


def _monday_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


