from calendar import monthrange
from datetime import date, timedelta
import re

from fastapi import HTTPException
from sqlalchemy import func, select
from uuid import UUID

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.db.models.m_payroll_period import PayrollPeriod
from app.schemas.sch_payroll_period import PayrollPeriodCreate, PayrollPeriodGenerateRequest
from app.util.payroll_period_key import period_key_from_dates


SUPPORTED_FREQUENCIES = {"weekly", "biweekly", "monthly", "semimonthly", "quarterly", "annually", "custom" }
ALLOWED_PERIOD_STATUSES = {"scheduled", "open", "closed"}


async def list_periods(zme: ZMeDataClass, skip: int = 0, limit: int = 100):
    """List all payroll periods with pagination."""
    query = (
        select(PayrollPeriod)
        .where(PayrollPeriod.biz_id == zme.zbid)
        .offset(skip)
        .limit(limit)
    )
    result = await zme.zdb.execute(query)
    return result.scalars().all()


async def create_period(payload: PayrollPeriodCreate, zme: ZMeDataClass):
    schedule = await _get_schedule(payload.payroll_schedule_id, zme)
    _validate_period_dates(payload.start_date, payload.end_date)
    _validate_status(payload.status)

    period_key = period_key_from_dates(schedule.frequency, payload.start_date, payload.end_date)
    pay_date = _pay_date_from_period(schedule, payload.end_date)

    period = PayrollPeriod(
        payroll_schedule_id=payload.payroll_schedule_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        pay_date=pay_date,
        period_key=period_key,
        status=payload.status,
        period_number=payload.period_number,
        biz_id=zme.zbid,
        ten_id=zme.ztid,
        owner_id=zme.zuid,
    )

    await _persist_period(period, zme)
    return period


async def generate_periods_for_schedule(
    payload: PayrollPeriodGenerateRequest,
    zme: ZMeDataClass,
):
    schedule = await _get_schedule(payload.payroll_schedule_id, zme)

    if payload.range_start > payload.range_end:
        raise HTTPException(status_code=400, detail="range_start must be on or before range_end")

    if schedule.frequency not in SUPPORTED_FREQUENCIES:
        allowed = ", ".join(sorted(SUPPORTED_FREQUENCIES))
        raise HTTPException(status_code=400, detail=f"Unsupported payroll frequency '{schedule.frequency}'. Allowed: {allowed}")

    starting_period_number = payload.starting_period_number
    if starting_period_number is None:
        max_period_number_query = select(func.max(PayrollPeriod.period_number)).where(
            PayrollPeriod.biz_id == zme.zbid,
            PayrollPeriod.payroll_schedule_id == schedule.id,
        )
        max_period_number_result = await zme.zdb.execute(max_period_number_query)
        max_period_number = max_period_number_result.scalar_one_or_none() or 0
        starting_period_number = max_period_number + 1

    generated_periods = _build_periods_from_schedule(
        schedule=schedule,
        range_start=payload.range_start,
        range_end=payload.range_end,
        starting_period_number=starting_period_number,
    )

    if not generated_periods:
        return []

    existing_query = select(PayrollPeriod.start_date).where(
        PayrollPeriod.biz_id == zme.zbid,
        PayrollPeriod.payroll_schedule_id == schedule.id,
        PayrollPeriod.start_date.in_([period.start_date for period in generated_periods]),
    )
    existing_result = await zme.zdb.execute(existing_query)
    existing_start_dates = set(existing_result.scalars().all())

    periods_to_create = [
        period for period in generated_periods if period.start_date not in existing_start_dates
    ]

    created_periods = []
    for period in periods_to_create:
        period.pay_date = _pay_date_from_period(schedule, period.end_date)
        period.period_key = period_key_from_dates(schedule.frequency, period.start_date, period.end_date)
        period.biz_id = zme.zbid
        period.ten_id = zme.ztid
        period.owner_id = zme.zuid
        await _persist_period(period, zme)
        created_periods.append(period)

    return created_periods


async def get_or_create_period_for_window(
    schedule: PayrollSchedule,
    period_start: date,
    period_end: date,
    zme: ZMeDataClass,
) -> PayrollPeriod:
    if period_start is None or period_end is None:
        raise HTTPException(status_code=400, detail="Payroll period window is missing")

    period_key = period_key_from_dates(schedule.frequency, period_start, period_end)
    query = select(PayrollPeriod).where(
        PayrollPeriod.biz_id == zme.zbid,
        PayrollPeriod.period_key == period_key,
    )
    result = await zme.zdb.execute(query)
    period = result.scalar_one_or_none()
    if period:
        return period

    max_period_number_query = select(func.max(PayrollPeriod.period_number)).where(
        PayrollPeriod.biz_id == zme.zbid,
        PayrollPeriod.payroll_schedule_id == schedule.id,
    )
    max_period_number_result = await zme.zdb.execute(max_period_number_query)
    max_period_number = max_period_number_result.scalar_one_or_none() or 0

    pay_date = _pay_date_from_period(schedule, period_end)
    period = PayrollPeriod(
        payroll_schedule_id=schedule.id,
        start_date=period_start,
        end_date=period_end,
        pay_date=pay_date,
        period_key=period_key,
        period_number=max_period_number + 1,
        status="open",
        biz_id=zme.zbid,
        ten_id=zme.ztid,
        owner_id=zme.zuid,
    )
    await _persist_period(period, zme)
    return period


async def reset_open_to_scheduled(period_id: UUID, zme: ZMeDataClass) -> PayrollPeriod:
    query = select(PayrollPeriod).where(PayrollPeriod.id == period_id,PayrollPeriod.biz_id == zme.zbid,)
    result = await zme.zdb.execute(query)
    period = result.scalar_one_or_none()
    if period is None:raise HTTPException(status_code=404, detail="Payroll period not found")

    if period.status == "open":
        period.status = "scheduled"
        await zme.zdb.flush()
        await zme.zdb.refresh(period)

    return period



async def open_period(period_id: UUID, zme: ZMeDataClass) -> PayrollPeriod:
    query = select(PayrollPeriod).where(PayrollPeriod.id == period_id,PayrollPeriod.biz_id == zme.zbid,)
    result = await zme.zdb.execute(query)
    period = result.scalar_one_or_none()
    if period is None:raise HTTPException(status_code=404, detail="Payroll period not found")

    if period.status == "scheduled":
        period.status = "open"
        await zme.zdb.flush()
        await zme.zdb.refresh(period)

    return period


async def _get_schedule(payroll_schedule_id, zme: ZMeDataClass) -> PayrollSchedule:
    query = select(PayrollSchedule).where(
        PayrollSchedule.id == payroll_schedule_id,
        PayrollSchedule.biz_id == zme.zbid,
    )
    result = await zme.zdb.execute(query)
    schedule = result.scalar_one_or_none()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Payroll schedule not found")
    return schedule


def _validate_period_dates(start_date: date, end_date: date) -> None:
    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")


def _validate_status(status: str) -> None:
    if status not in ALLOWED_PERIOD_STATUSES:
        allowed = ", ".join(sorted(ALLOWED_PERIOD_STATUSES))
        raise HTTPException(status_code=400, detail=f"Unsupported status '{status}'. Allowed: {allowed}")


def _build_periods_from_schedule(
    schedule: PayrollSchedule,
    range_start: date,
    range_end: date,
    starting_period_number: int | None,
) -> list[PayrollPeriod]:
    if schedule.frequency == "weekly":
        windows = _build_fixed_windows(schedule.anchor_date, range_start, range_end, 7)
    elif schedule.frequency == "biweekly":
        windows = _build_fixed_windows(schedule.anchor_date, range_start, range_end, 14)
    elif schedule.frequency == "monthly":
        windows = _build_monthly_windows(schedule.anchor_date, range_start, range_end)
    else:
        windows = _build_semimonthly_windows(schedule.anchor_date, range_start, range_end)

    windows = [
        (start_date, end_date)
        for start_date, end_date in windows
        if _is_window_within_schedule(schedule, start_date, end_date)
    ]

    first_period_number = starting_period_number or 1

    return [
        PayrollPeriod(
            payroll_schedule_id=schedule.id,
            start_date=start_date,
            end_date=end_date,
            status="scheduled",
            period_number=first_period_number + index,
        )
        for index, (start_date, end_date) in enumerate(windows)
    ]


def _build_fixed_windows(
    anchor_date: date,
    range_start: date,
    range_end: date,
    cycle_days: int,
) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    current_start = anchor_date

    while current_start <= range_end:
        current_end = current_start + timedelta(days=cycle_days - 1)
        if current_start >= range_start and current_end <= range_end:
            windows.append((current_start, current_end))
        current_start = current_start + timedelta(days=cycle_days)

    return windows


def _build_monthly_windows(
    anchor_date: date,
    range_start: date,
    range_end: date,
) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    year = anchor_date.year
    month = anchor_date.month
    current_start = anchor_date

    while current_start <= range_end:
        next_year, next_month = _next_month(year, month)
        next_start = _safe_date(next_year, next_month, anchor_date.day)
        current_end = next_start - timedelta(days=1)
        if current_start >= range_start and current_end <= range_end:
            windows.append((current_start, current_end))
        year, month = next_year, next_month
        current_start = next_start

    return windows


def _build_semimonthly_windows(
    anchor_date: date,
    range_start: date,
    range_end: date,
) -> list[tuple[date, date]]:
    windows: list[tuple[date, date]] = []
    current = date(anchor_date.year, anchor_date.month, 1)

    while current <= range_end:
        days_in_month = monthrange(current.year, current.month)[1]
        first_half_end = min(anchor_date.day, days_in_month)
        second_half_start = first_half_end + 1

        first_start = date(current.year, current.month, 1)
        first_end = date(current.year, current.month, first_half_end)
        if first_start >= range_start and first_end <= range_end:
            windows.append((first_start, first_end))

        if second_half_start <= days_in_month:
            second_start = date(current.year, current.month, second_half_start)
            second_end = date(current.year, current.month, days_in_month)
            if second_start >= range_start and second_end <= range_end:
                windows.append((second_start, second_end))

        next_year, next_month = _next_month(current.year, current.month)
        current = date(next_year, next_month, 1)

    return windows


def _is_window_within_schedule(schedule: PayrollSchedule, start_date: date, end_date: date) -> bool:
    if start_date < schedule.effective_from:
        return False
    if schedule.effective_to and end_date > schedule.effective_to:
        return False
    return True


def _safe_date(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, monthrange(year, month)[1]))


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


async def _persist_period(period: PayrollPeriod, zme: ZMeDataClass) -> None:
    zme.zdb.add(period)
    await zme.zdb.flush()
    await zme.zdb.refresh(period)


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


