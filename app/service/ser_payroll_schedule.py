from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_employee import EmployeeDB
from app.db.models.t4.m_payroll_entry import PayrollEntryDB
from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.db.repo.repo_payroll_schedule import list_payroll_schedules
from app.db.repo.repo_utils import coerce_model_values
from app.schemas.sch_ai import JWType
from app.schemas.sch_payroll_schedule import PayrollScheduleUpsert
from app.service.ser_payroll_common import (
    deductions_on_2026,
    period_key,
    period_frequency,
)
from app.service.ser_payroll_period import get_or_create_period_for_window


async def fetch_payroll_schedules(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollScheduleDB]:
    return await list_payroll_schedules(db, sbu_client_id)


async def create_or_update_payroll_schedule(
    zjwt: JWType,
    db: AsyncSession,
    payload: PayrollScheduleUpsert,
) -> PayrollScheduleDB:
    sbu_client_id = zjwt.zcid
    if sbu_client_id is None:
        raise HTTPException(status_code=400, detail="Missing sbu_client_id in JWT.")

    actor_id = zjwt.zuid
    if actor_id is None:
        raise HTTPException(status_code=400, detail="Missing user id in JWT.")

    ten_id = zjwt.ztid
    values = payload.model_dump(exclude_unset=True)
    schedule_id = values.get("id")

    existing = None
    previous_status = "inactive"
    if schedule_id:
        result = await db.execute(
            select(PayrollScheduleDB).where(
                PayrollScheduleDB.id == schedule_id,
                PayrollScheduleDB.cli_id == sbu_client_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            previous_status = (existing.status or "").lower()
            for key, value in coerce_model_values(existing, values).items():
                if key != "id":
                    setattr(existing, key, value)
            existing.cli_id = sbu_client_id
            existing.biz_id = sbu_client_id
            existing.ten_id = ten_id or existing.ten_id
            existing.usr_id = actor_id
            existing.created_by = actor_id
            schedule = existing
        else:
            schedule = PayrollScheduleDB(
                **coerce_model_values(
                    PayrollScheduleDB,
                    {
                        **values,
                        "id": schedule_id,
                        "cli_id": sbu_client_id,
                        "biz_id": sbu_client_id,
                        "ten_id": ten_id,
                        "usr_id": actor_id,
                        "created_by": actor_id,
                    },
                )
            )
            db.add(schedule)
    else:
        schedule = PayrollScheduleDB(
            **coerce_model_values(
                PayrollScheduleDB,
                {
                    **values,
                    "cli_id": sbu_client_id,
                    "biz_id": sbu_client_id,
                    "ten_id": ten_id,
                    "usr_id": actor_id,
                    "created_by": actor_id,
                },
            )
        )
        db.add(schedule)

    await db.flush()

    incoming_status = (schedule.status or "").lower()
    if previous_status == "active" and incoming_status == "inactive":
        has_entries_result = await db.execute(
            select(PayrollEntryDB.id).where(
                PayrollEntryDB.schedule_id == schedule.id,
                PayrollEntryDB.cli_id == sbu_client_id,
            )
        )
        has_entries = has_entries_result.scalars().first() is not None
        if has_entries:
            raise HTTPException(
                status_code=409,
                detail="Cannot set schedule to inactive while payroll entries exist for this schedule",
            )
    elif previous_status == "inactive" and incoming_status == "active":
        await _reset_entries_for_schedule(schedule, db, sbu_client_id)
    elif incoming_status == "active":
        await _recalculate_entries_for_schedule(schedule, db, sbu_client_id)

    await db.flush()
    await db.refresh(schedule)
    return schedule


async def _recalculate_entries_for_schedule(
    schedule: PayrollScheduleDB,
    db: AsyncSession,
    sbu_client_id: UUID,
) -> None:
    result = await db.execute(
        select(PayrollEntryDB).where(
            PayrollEntryDB.schedule_id == schedule.id,
            PayrollEntryDB.cli_id == sbu_client_id,
        )
    )
    entries = list(result.scalars().all())
    if not entries:
        return

    periods_per_year = period_frequency(schedule.frequency)
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
        deductions = deductions_on_2026(
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


async def _reset_entries_for_schedule(
    schedule: PayrollScheduleDB,
    db: AsyncSession,
    sbu_client_id: UUID,
) -> None:
    await db.execute(delete(PayrollEntryDB).where(PayrollEntryDB.cli_id == sbu_client_id))
    period_start, period_end = _current_period_window(schedule)
    pay_date = _pay_date_from_period(schedule, period_end)
    await _create_entries_for_schedule(
        schedule=schedule,
        db=db,
        sbu_client_id=sbu_client_id,
        period_start=period_start,
        period_end=period_end,
        pay_date=pay_date,
    )


async def _create_entries_for_schedule(
    schedule: PayrollScheduleDB,
    db: AsyncSession,
    sbu_client_id: UUID,
    period_start: date | None = None,
    period_end: date | None = None,
    pay_date: date | None = None,
) -> None:
    employee_result = await db.execute(
        select(EmployeeDB).where(
            EmployeeDB.cli_id == sbu_client_id,
            or_(EmployeeDB.is_deleted.is_(None), EmployeeDB.is_deleted.is_(False)),
        )
    )
    employees = list(employee_result.scalars().all())
    if not employees:
        return

    period = None
    period_key_value = None
    if period_start and period_end:
        period = await get_or_create_period_for_window(
            db=db,
            schedule=schedule,
            period_start=period_start,
            period_end=period_end,
            sbu_client_id=sbu_client_id,
        )
        period_key_value = period.period_key
        pay_date = period.pay_date

    if period_key_value is None and period_start and period_end:
        period_key_value = period_key(schedule.frequency, period_start, period_end)
    if pay_date is None:
        pay_date = _pay_date_from_period(schedule, period_end)

    periods_per_year = period_frequency(schedule.frequency)
    for employee in employees:
        employment_type = (employee.employment_type or "other").lower()
        full_name = " ".join(part for part in [employee.first_name, employee.last_name] if part)
        gross = Decimal("0.00")
        if employment_type == "salary" and employee.annual_salary is not None:
            gross = (employee.annual_salary / periods_per_year).quantize(Decimal("0.01"))
        elif employment_type == "hourly" and employee.regular_hours is not None and employee.hourly_rate is not None:
            gross = (employee.regular_hours * employee.hourly_rate).quantize(Decimal("0.01"))

        deductions = deductions_on_2026(
            period_gross=gross,
            periods_per_year=periods_per_year,
            cpp_exempt=bool(employee.cpp_exempt),
            ei_exempt=bool(employee.ei_exempt),
            federal_basic_personal_amount=employee.federal_claim_amount,
            ontario_basic_personal_amount=employee.ontario_claim_amount,
        )

        db.add(
            PayrollEntryDB(
                schedule_id=schedule.id,
                payroll_period_id=period.id if period else None,
                employee_id=employee.id,
                period_start=period_start,
                period_end=period_end,
                pay_date=pay_date,
                period_key=period_key_value,
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
                cli_id=sbu_client_id,
                biz_id=sbu_client_id,
                ten_id=schedule.ten_id or schedule.cli_id,
                usr_id=schedule.usr_id,
                created_by=schedule.created_by,
            )
        )
    await db.flush()


def _current_period_window(schedule: PayrollScheduleDB) -> tuple[date | None, date | None]:
    freq = (schedule.frequency or "").lower()
    if freq not in {"weekly", "biweekly", "monthly", "semimonthly"}:
        return None, None

    effective = schedule.effective_from or date.today()
    if freq == "monthly":
        return date(effective.year, effective.month, 1), date(
            effective.year, effective.month, monthrange(effective.year, effective.month)[1]
        )
    if freq == "semimonthly":
        last_day = monthrange(effective.year, effective.month)[1]
        if effective.day <= 15:
            return date(effective.year, effective.month, 1), date(effective.year, effective.month, 15)
        return date(effective.year, effective.month, 16), date(effective.year, effective.month, last_day)
    if freq == "weekly":
        period_start = _monday_of_week(effective)
        return period_start, period_start + timedelta(days=4)
    period_start = _monday_of_week(effective)
    return period_start, period_start + timedelta(days=11)


def _pay_date_from_period(schedule: PayrollScheduleDB, period_end: date | None) -> date | None:
    if period_end is None:
        return None

    payon_raw = (schedule.payon or "").strip().lower()
    if not payon_raw:
        return period_end
    if payon_raw in {"eom", "end of month", "last day of month", "month end"}:
        return date(period_end.year, period_end.month, monthrange(period_end.year, period_end.month)[1])

    if any(char.isdigit() for char in payon_raw):
        day = int("".join(ch for ch in payon_raw if ch.isdigit()))
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
    if payon_raw in weekday_map:
        target = weekday_map[payon_raw]
        days_ahead = (target - period_end.weekday()) % 7
        return period_end + timedelta(days=days_ahead)
    return period_end


def _monday_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _to_uuid_or_none(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except ValueError:
        return None
