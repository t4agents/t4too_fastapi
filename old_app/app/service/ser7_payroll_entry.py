from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_employee import Employee
from app.db.models.m_payroll_entry import PayrollEntry
from app.db.models.m_payroll_history import PayrollHistory
from app.db.models.m_payroll_period import PayrollPeriod
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.db.models.ai_embedding import Embedding384
from app.db.repo.repo_payroll_entry import PayrollEntryRepository
from app.schemas.sch_payroll_entry import PayrollEntryAddEmployeesRequest, PayrollEntryCreate, PayrollEntryUpdate
from app.service.payroll_period import get_or_create_period_for_window
from app.service.ser5_payroll_schedule import (
    _create_entries_for_schedule,
    _current_period_window,
    _pay_date_from_period,
)
from app.util.payroll_calc_on_2026 import (calculate_payroll_deductions_on_2026,periods_per_year_from_frequency,)
from app.util.payroll_period_key import period_key_from_dates
from app.llm.conn.openai_embedder import embed_fn


async def list_current_entry_employees(zme: ZMeDataClass,skip: int = 0,limit: int = 100,) -> List[PayrollEntry]:
    query = select(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid)
    result = await zme.zdb.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def edit_entry(payload: PayrollEntryUpdate, zme: ZMeDataClass) -> PayrollEntry:
    query = select(PayrollEntry).where(PayrollEntry.id == payload.id, PayrollEntry.biz_id == zme.zbid,)
    result = await zme.zdb.execute(query)
    entry = result.scalars().first()
    if not entry:raise HTTPException(status_code=404, detail="Payroll entry not found")

    immutable_fields = {"id","biz_id","ten_id","owner_id","employee_id","schedule_id","period_key",}
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key in immutable_fields:
            continue
        setattr(entry, key, value)

    await zme.zdb.flush()
    await _recalculate_entry_deductions(entry, zme)
    await zme.zdb.flush()
    await zme.zdb.refresh(entry)
    return entry


async def _recalculate_entry_deductions(entry: PayrollEntry, zme: ZMeDataClass) -> None:
    if not entry.schedule_id:
        return

    schedule_result = await zme.zdb.execute(
        select(PayrollSchedule).where(
            PayrollSchedule.id == entry.schedule_id,
            PayrollSchedule.biz_id == zme.zbid,
        )
    )
    schedule = schedule_result.scalars().first()
    if not schedule:
        return

    periods_per_year = periods_per_year_from_frequency(schedule.frequency)

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


def _format_chunk_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _chunk(history: PayrollHistory) -> str:
    parts = [
        "payroll_history",
        f"full_name={_format_chunk_value(history.full_name)}",
        f"employment_type={_format_chunk_value(history.employment_type)}",
        f"period_start={_format_chunk_value(history.period_start)}",
        f"period_end={_format_chunk_value(history.period_end)}",
        f"period_key={_format_chunk_value(history.period_key)}",
        f"pay_date={_format_chunk_value(history.pay_date)}",
        f"annual_salary_snapshot={_format_chunk_value(history.annual_salary_snapshot)}",
        f"hourly_rate_snapshot={_format_chunk_value(history.hourly_rate_snapshot)}",
        f"federal_claim_snapshot={_format_chunk_value(history.federal_claim_snapshot)}",
        f"ontario_claim_snapshot={_format_chunk_value(history.ontario_claim_snapshot)}",
        f"regular_hours={_format_chunk_value(history.regular_hours)}",
        f"overtime_hours={_format_chunk_value(history.overtime_hours)}",
        f"bonus={_format_chunk_value(history.bonus)}",
        f"vacation={_format_chunk_value(history.vacation)}",
        f"cpp={_format_chunk_value(history.cpp)}",
        f"ei={_format_chunk_value(history.ei)}",
        f"tax={_format_chunk_value(history.tax)}",
        f"gross={_format_chunk_value(history.gross)}",
        f"total_deduction={_format_chunk_value(history.total_deduction)}",
        f"adjustment={_format_chunk_value(history.adjustment)}",
        f"net={_format_chunk_value(history.net)}",
        f"cpp_exempt_snapshot={_format_chunk_value(history.cpp_exempt_snapshot)}",
        f"ei_exempt_snapshot={_format_chunk_value(history.ei_exempt_snapshot)}",
        f"excluded={_format_chunk_value(history.excluded)}",
        f"status={_format_chunk_value(history.status)}",
    ]
    return " | ".join(parts)


async def _embedding(text: str) -> list[float]:
    return await embed_fn(text)


async def finalize_entry(zme: ZMeDataClass,):
    entry_result = await zme.zdb.execute(select(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid))
    entries = entry_result.scalars().all()
    if not entries:raise HTTPException(status_code=404, detail="No payroll entries to finalize")

    first_entry = entries[0]
    if first_entry.period_start is None or first_entry.period_end is None:
        raise HTTPException(status_code=400, detail="Payroll entries are missing period_start/period_end")

    schedule_result = await zme.zdb.execute(
        select(PayrollSchedule).where(
            PayrollSchedule.id == first_entry.schedule_id,
            PayrollSchedule.biz_id == zme.zbid,
        )
    )
    schedule = schedule_result.scalars().first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Payroll schedule not found")

    period = None
    if first_entry.payroll_period_id:
        period_result = await zme.zdb.execute(
            select(PayrollPeriod).where(
                PayrollPeriod.id == first_entry.payroll_period_id,
                PayrollPeriod.biz_id == zme.zbid,
            )
        )
        period = period_result.scalars().first()
    if not period:
        period = await get_or_create_period_for_window(
            schedule,
            first_entry.period_start,
            first_entry.period_end,
            zme,
        )
    if period.status == "closed":
        raise HTTPException(status_code=409, detail="Payroll period already finalized")

    zero = Decimal("0.00")
    history_rows = [
        PayrollHistory(
            schedule_id=entry.schedule_id,
            payroll_period_id=period.id,
            employee_id=entry.employee_id,
            full_name=entry.full_name,
            employment_type=entry.employment_type,
            
            period_start=entry.period_start,
            period_end=entry.period_end,
            period_key=entry.period_key,
            pay_date=entry.pay_date,
            
            annual_salary_snapshot=zero if entry.excluded else entry.annual_salary_snapshot,
            hourly_rate_snapshot=zero if entry.excluded else entry.hourly_rate_snapshot,
            federal_claim_snapshot=zero if entry.excluded else (entry.federal_claim_snapshot or zero),
            ontario_claim_snapshot=zero if entry.excluded else (entry.ontario_claim_snapshot or zero),
            regular_hours=zero if entry.excluded else entry.regular_hours,
            overtime_hours=zero if entry.excluded else entry.overtime_hours,
            bonus=zero if entry.excluded else (entry.bonus or zero),
            vacation=zero if entry.excluded else (entry.vacation or zero),
            cpp=zero if entry.excluded else (entry.cpp or zero),
            ei=zero if entry.excluded else (entry.ei or zero),
            tax=zero if entry.excluded else (entry.tax or zero),
            gross=zero if entry.excluded else entry.gross,
            total_deduction=zero if entry.excluded else entry.total_deduction,
            adjustment=zero if entry.excluded else entry.adjustment,
            net=zero if entry.excluded else entry.net,
            cpp_exempt_snapshot=bool(entry.cpp_exempt_snapshot),
            ei_exempt_snapshot=bool(entry.ei_exempt_snapshot),
            excluded=bool(entry.excluded),
            status="finalized",
            biz_id=zme.zbid,
            ten_id=zme.ztid,
            owner_id=zme.zuid,
        )
        for entry in entries
    ]

    zme.zdb.add_all(history_rows)
    period.status = "closed"
    await zme.zdb.flush()

    embedding_rows: list[Embedding384] = []
    for history in history_rows:
        chunk_text = _chunk(history)
        emb = await _embedding(chunk_text)
        embedding_rows.append(
            Embedding384(
                source_id=history.id,
                chunk=chunk_text,
                emb384=emb,
            )
        )
    if embedding_rows:
        zme.zdb.add_all(embedding_rows)
        await zme.zdb.flush()

    await zme.zdb.execute(delete(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid))
    await zme.zdb.flush()

    next_start, next_end = _next_period_window(
        schedule.frequency,
        first_entry.period_start,
        first_entry.period_end,
    )
    await _create_entries_for_schedule(
        schedule,
        zme,
        period_start=next_start,
        period_end=next_end,
    )
    await zme.zdb.flush()

    first_key = first_entry.period_key
    return {"period_key": first_key}


async def add_entry_employees(
    payload: PayrollEntryAddEmployeesRequest,
    zme: ZMeDataClass,
) -> List[PayrollEntry]:
    if not payload.employee_ids:
        raise HTTPException(status_code=400, detail="employee_ids is required")

    entry_result = await zme.zdb.execute(
        select(PayrollEntry)
        .where(PayrollEntry.biz_id == zme.zbid)
        .order_by(PayrollEntry.created_at.desc())
        .limit(1)
    )
    base_entry = entry_result.scalars().first()

    schedule = None
    if base_entry:
        schedule_id = base_entry.schedule_id
        period_start = base_entry.period_start
        period_end = base_entry.period_end
        period_key = base_entry.period_key
        pay_date = base_entry.pay_date

        schedule_result = await zme.zdb.execute(
            select(PayrollSchedule).where(
                PayrollSchedule.id == schedule_id,
                PayrollSchedule.biz_id == zme.zbid,
            )
        )
        schedule = schedule_result.scalars().first()
    else:
        schedule_result = await zme.zdb.execute(
            select(PayrollSchedule).where(
                PayrollSchedule.biz_id == zme.zbid,
                PayrollSchedule.status == "active",
            )
        )
        schedule = schedule_result.scalars().first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Active payroll schedule not found")

        period_start, period_end = _current_period_window(schedule)
        if period_start is None or period_end is None:
            raise HTTPException(status_code=400, detail="Payroll schedule period is not initialized")
        period_key = period_key_from_dates(schedule.frequency, period_start, period_end)
        pay_date = _pay_date_from_period(schedule, period_end)
        schedule_id = schedule.id

    if not schedule:
        raise HTTPException(status_code=404, detail="Payroll schedule not found")

    period = None
    if period_start and period_end:
        period = await get_or_create_period_for_window(
            schedule,
            period_start,
            period_end,
            zme,
        )
        period_key = period.period_key
        pay_date = period.pay_date
        if period.status == "closed":
            raise HTTPException(status_code=409, detail="Payroll period already finalized")

    employee_query = select(Employee).where(
        Employee.biz_id == zme.zbid,
        Employee.id.in_(payload.employee_ids),
        or_(Employee.is_deleted.is_(None), Employee.is_deleted.is_(False)),
    )
    employee_result = await zme.zdb.execute(employee_query)
    employees = employee_result.scalars().all()
    found_ids = {employee.id for employee in employees}
    missing_ids = [str(employee_id) for employee_id in payload.employee_ids if employee_id not in found_ids]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Employees not found: {', '.join(missing_ids)}",
        )

    periods_per_year = periods_per_year_from_frequency(schedule.frequency)
    entries: list[PayrollEntry] = []
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
                schedule_id=schedule_id,
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

    return entries


def _next_month(year: int, month: int) -> tuple[int, int]:
    if month == 12:
        return year + 1, 1
    return year, month + 1


def _next_period_window(
    frequency: str | None,
    period_start: date,
    period_end: date,
) -> tuple[date, date]:
    freq = (frequency or "").lower()
    if freq == "monthly":
        next_year, next_month = _next_month(period_end.year, period_end.month)
        start = date(next_year, next_month, 1)
        end = date(next_year, next_month, monthrange(next_year, next_month)[1])
        return start, end
    if freq == "semimonthly":
        if period_start.day <= 15:
            last_day = monthrange(period_start.year, period_start.month)[1]
            return date(period_start.year, period_start.month, 16), date(period_start.year, period_start.month, last_day)
        next_year, next_month = _next_month(period_start.year, period_start.month)
        return date(next_year, next_month, 1), date(next_year, next_month, 15)
    if freq == "weekly":
        start = period_start + timedelta(days=7)
        end = start + timedelta(days=4)
        return start, end
    if freq == "biweekly":
        start = period_start + timedelta(days=14)
        end = start + timedelta(days=11)
        return start, end
    raise HTTPException(status_code=400, detail=f"Unsupported payroll frequency '{freq}'")
