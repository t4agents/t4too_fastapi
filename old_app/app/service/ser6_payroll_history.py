from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from typing import List
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import case, delete, func, select

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_payroll_entry import PayrollEntry
from app.db.models.m_payroll_history import PayrollHistory
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.schemas.sch_payroll_history import (
    HistoryDetailResponse,
    HistoryListRow,
    PayrollHistoryEntryResponse,
)
from app.service.ser5_payroll_schedule import _create_entries_for_schedule
from app.util.payroll_period_key import period_key_from_dates


async def list_history(zme: ZMeDataClass,) -> List[HistoryListRow]:
    query = (
        select(
            PayrollHistory.schedule_id,
            PayrollHistory.period_start,
            PayrollHistory.period_end,
            PayrollHistory.period_key,
            PayrollHistory.pay_date.label("pay_day"),
            func.sum(PayrollHistory.gross).label("total_gross"),
            func.sum(PayrollHistory.total_deduction).label("total_deduction"),
            func.sum(PayrollHistory.net).label("total_net"),
            func.count(PayrollHistory.employee_id).label("employee_count"),
            func.sum(
                case((PayrollHistory.excluded.is_(True), 1), else_=0)
            ).label("excluded_count"),
        )
        .where(PayrollHistory.biz_id == zme.zbid)
        .group_by(
            PayrollHistory.schedule_id,
            PayrollHistory.period_start,
            PayrollHistory.period_end,
            PayrollHistory.period_key,
            PayrollHistory.pay_date,
        )
        .order_by(PayrollHistory.period_end.desc())
    )

    result = await zme.zdb.execute(query)
    rows = result.all()

    summaries: List[HistoryListRow] = []
    for row in rows:
        total_gross = _sum_or_zero(row.total_gross)
        total_deduction = _sum_or_zero(row.total_deduction)
        total_net = _sum_or_zero(row.total_net)
        summaries.append(
            HistoryListRow(
                schedule_id=row.schedule_id,
                period_start=row.period_start,
                period_end=row.period_end,
                period_key=row.period_key,
                pay_day=row.pay_day,
                status="finalized",
                total_gross=total_gross,
                payroll_cost=total_gross,
                total_net=total_net,
                taxes_and_deductions=total_deduction,
                employee_count=int(row.employee_count or 0),
                excluded_count=int(row.excluded_count or 0),
            )
        )
    return summaries




def _sum_or_zero(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0.00")


# async def finalize_payroll(payload: PayrollHistoryFinalizeRequest, zme: ZMe_DataClass) -> PayrollHistorySummaryResponse:
#     schedule_result = await zme.zdb.execute(
#         select(PayrollSchedule).where(
#             PayrollSchedule.id == payload.schedule_id,
#             PayrollSchedule.biz_id == zme.zbid,
#         )
#     )
#     schedule = schedule_result.scalars().first()
#     if not schedule:
#         raise HTTPException(status_code=404, detail="Payroll schedule not found")

#     entry_result = await zme.zdb.execute(
#         select(PayrollEntry).where(
#             PayrollEntry.schedule_id == payload.schedule_id,
#             PayrollEntry.biz_id == zme.zbid,
#         )
#     )
#     entries = entry_result.scalars().all()
#     if not entries:
#         raise HTTPException(status_code=404, detail="No payroll entries to finalize")

#     entry_periods = {(entry.period_start, entry.period_end) for entry in entries}
#     if None in {p for pair in entry_periods for p in pair}:
#         raise HTTPException(status_code=400, detail="Payroll entries are missing period_start/period_end")
#     if len(entry_periods) != 1:
#         raise HTTPException(status_code=400, detail="Payroll entries span multiple periods")
#     entry_period = next(iter(entry_periods))
#     if entry_period != (payload.period_start, payload.period_end):
#         raise HTTPException(status_code=400, detail="Finalize period does not match current payroll entries")
#     derived_key = period_key_from_dates(
#         schedule.frequency,
#         payload.period_start,
#         payload.period_end,
#     )
#     if payload.period_key != derived_key:
#         raise HTTPException(status_code=400, detail="Finalize period_key does not match payroll schedule")

#     entry_keys = {
#         entry.period_key
#         or period_key_from_dates(
#             schedule.frequency,
#             entry.period_start,
#             entry.period_end,
#         )
#         for entry in entries
#     }
#     if len(entry_keys) != 1 or payload.period_key not in entry_keys:
#         raise HTTPException(status_code=400, detail="Payroll entries span multiple period keys")

#     history_rows = [
#         PayrollHistory(
#             schedule_id=entry.schedule_id,
#             employee_id=entry.employee_id,
#             period_start=payload.period_start,
#             period_end=payload.period_end,
#             period_key=payload.period_key,
#             pay_date=payload.pay_day,
#             employment_type=entry.employment_type,
#             full_name=entry.full_name,
#             annual_salary_snapshot=entry.annual_salary_snapshot,
#             hourly_rate_snapshot=entry.hourly_rate_snapshot,
#             federal_claim_snapshot=entry.federal_claim_snapshot or Decimal("0.00"),
#             ontario_claim_snapshot=entry.ontario_claim_snapshot or Decimal("0.00"),
#             regular_hours=entry.regular_hours,
#             overtime_hours=entry.overtime_hours,
#             bonus=entry.bonus or Decimal("0.00"),
#             vacation=entry.vacation or Decimal("0.00"),
#             cpp=entry.cpp or Decimal("0.00"),
#             ei=entry.ei or Decimal("0.00"),
#             tax=entry.tax or Decimal("0.00"),
#             gross=entry.gross,
#             total_deduction=entry.total_deduction,
#             adjustment=entry.adjustment,
#             net=entry.net,
#             cpp_exempt_snapshot=bool(entry.cpp_exempt_snapshot),
#             ei_exempt_snapshot=bool(entry.ei_exempt_snapshot),
#             status="finalized",
#             biz_id=zme.zbid,
#             ten_id=zme.ztid,
#             owner_id=zme.zuid,
#         )
#         for entry in entries
#     ]

#     zme.zdb.add_all(history_rows)
#     await zme.zdb.flush()

#     await zme.zdb.execute(
#         delete(PayrollEntry).where(
#             PayrollEntry.schedule_id == payload.schedule_id,
#             PayrollEntry.biz_id == zme.zbid,
#         )
#     )

#     next_start, next_end = _advance_period(
#         frequency=schedule.frequency,
#         period_start=payload.period_start,
#         period_end=payload.period_end,
#     )
#     await _create_entries_for_schedule(
#         schedule,
#         zme,
#         period_start=next_start,
#         period_end=next_end,
#     )
#     await zme.zdb.flush()

#     summary = await _history_summary(
#         zme=zme,
#         schedule_id=payload.schedule_id,
#         period_key=payload.period_key,
#     )
#     if summary is None:
#         raise HTTPException(status_code=500, detail="Failed to finalize payroll history")
#     return summary


# async def finalize_payroll_from_entries(
#     schedule_id: UUID,
#     pay_day: date | None,
#     zme: ZMe_DataClass,
# ) -> PayrollHistorySummaryResponse:
#     schedule_result = await zme.zdb.execute(
#         select(PayrollSchedule).where(
#             PayrollSchedule.id == schedule_id,
#             PayrollSchedule.biz_id == zme.zbid,
#         )
#     )
#     schedule = schedule_result.scalars().first()
#     if not schedule:
#         raise HTTPException(status_code=404, detail="Payroll schedule not found")

#     entry_result = await zme.zdb.execute(
#         select(PayrollEntry).where(
#             PayrollEntry.schedule_id == schedule_id,
#             PayrollEntry.biz_id == zme.zbid,
#         )
#     )
#     entries = entry_result.scalars().all()
#     if not entries:
#         raise HTTPException(status_code=404, detail="No payroll entries to finalize")

#     entry_periods = {(entry.period_start, entry.period_end) for entry in entries}
#     if None in {p for pair in entry_periods for p in pair}:
#         raise HTTPException(status_code=400, detail="Payroll entries are missing period_start/period_end")
#     if len(entry_periods) != 1:
#         raise HTTPException(status_code=400, detail="Payroll entries span multiple periods")
#     period_start, period_end = next(iter(entry_periods))

#     entry_keys = {
#         entry.period_key
#         or period_key_from_dates(
#             schedule.frequency,
#             entry.period_start,
#             entry.period_end,
#         )
#         for entry in entries
#     }
#     if len(entry_keys) != 1:
#         raise HTTPException(status_code=400, detail="Payroll entries span multiple period keys")
#     period_key = next(iter(entry_keys))

#     history_rows = [
#         PayrollHistory(
#             schedule_id=entry.schedule_id,
#             employee_id=entry.employee_id,
#             period_start=period_start,
#             period_end=period_end,
#             period_key=period_key,
#             pay_date=pay_day,
#             employment_type=entry.employment_type,
#             full_name=entry.full_name,
#             annual_salary_snapshot=entry.annual_salary_snapshot,
#             hourly_rate_snapshot=entry.hourly_rate_snapshot,
#             federal_claim_snapshot=entry.federal_claim_snapshot or Decimal("0.00"),
#             ontario_claim_snapshot=entry.ontario_claim_snapshot or Decimal("0.00"),
#             regular_hours=entry.regular_hours,
#             overtime_hours=entry.overtime_hours,
#             bonus=entry.bonus or Decimal("0.00"),
#             vacation=entry.vacation or Decimal("0.00"),
#             cpp=entry.cpp or Decimal("0.00"),
#             ei=entry.ei or Decimal("0.00"),
#             tax=entry.tax or Decimal("0.00"),
#             gross=entry.gross,
#             total_deduction=entry.total_deduction,
#             adjustment=entry.adjustment,
#             net=entry.net,
#             cpp_exempt_snapshot=bool(entry.cpp_exempt_snapshot),
#             ei_exempt_snapshot=bool(entry.ei_exempt_snapshot),
#             status="finalized",
#             biz_id=zme.zbid,
#             ten_id=zme.ztid,
#             owner_id=zme.zuid,
#         )
#         for entry in entries
#     ]

#     zme.zdb.add_all(history_rows)
#     await zme.zdb.flush()

#     await zme.zdb.execute(
#         delete(PayrollEntry).where(
#             PayrollEntry.schedule_id == schedule_id,
#             PayrollEntry.biz_id == zme.zbid,
#         )
#     )

#     next_start, next_end = _advance_period(
#         frequency=schedule.frequency,
#         period_start=period_start,
#         period_end=period_end,
#     )
#     await _create_entries_for_schedule(
#         schedule,
#         zme,
#         period_start=next_start,
#         period_end=next_end,
#     )
#     await zme.zdb.flush()

#     summary = await _history_summary(
#         zme=zme,
#         schedule_id=schedule_id,
#         period_key=period_key,
#     )
#     if summary is None:
#         raise HTTPException(status_code=500, detail="Failed to finalize payroll history")
#     return summary


# async def finalize_payroll_from_entries_for_biz(zme: ZMe_DataClass) -> PayrollHistorySummaryResponse:
#     entry_result = await zme.zdb.execute(
#         select(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid)
#     )
#     entries = entry_result.scalars().all()
#     if not entries:
#         raise HTTPException(status_code=404, detail="No payroll entries to finalize")

#     first_entry = entries[0]
#     schedule_id = first_entry.schedule_id

#     schedule_result = await zme.zdb.execute(
#         select(PayrollSchedule).where(
#             PayrollSchedule.id == schedule_id,
#             PayrollSchedule.biz_id == zme.zbid,
#         )
#     )
#     schedule = schedule_result.scalars().first()
#     if not schedule:
#         raise HTTPException(status_code=404, detail="Payroll schedule not found")

#     if first_entry.period_start is None or first_entry.period_end is None:
#         raise HTTPException(status_code=400, detail="Payroll entries are missing period_start/period_end")
#     period_start, period_end = first_entry.period_start, first_entry.period_end
#     period_key = first_entry.period_key or period_key_from_dates(
#         schedule.frequency,
#         period_start,
#         period_end,
#     )

#     history_rows = [
#         PayrollHistory(
#             schedule_id=entry.schedule_id,
#             employee_id=entry.employee_id,
#             period_start=entry.period_start,
#             period_end=entry.period_end,
#             period_key=entry.period_key
#             or period_key_from_dates(
#                 schedule.frequency,
#                 entry.period_start,
#                 entry.period_end,
#             ),
#             pay_date=entry.pay_date,
#             employment_type=entry.employment_type,
#             full_name=entry.full_name,
#             annual_salary_snapshot=entry.annual_salary_snapshot,
#             hourly_rate_snapshot=entry.hourly_rate_snapshot,
#             federal_claim_snapshot=entry.federal_claim_snapshot or Decimal("0.00"),
#             ontario_clapay_dayhot=entry.ontario_claim_snapshot or Decimal("0.00"),
#             regular_hours=entry.regular_hours,
#             overtime_hours=entry.overtime_hours,
#             bonus=entry.bonus or Decimal("0.00"),
#             vacation=entry.vacation or Decimal("0.00"),
#             cpp=entry.cpp or Decimal("0.00"),
#             ei=entry.ei or Decimal("0.00"),
#             tax=entry.tax or Decimal("0.00"),
#             gross=entry.gross,
#             total_deduction=entry.total_deduction,
#             adjustment=entry.adjustment,
#             net=entry.net,
#        pay_day_exempt_snapshot=bool(entry.cpp_exempt_snapshot),
#             ei_exempt_snapshot=bool(entry.ei_exempt_snapshot),
#             status="finalized",
#             biz_id=zme.zbid,
#             ten_id=zme.ztid,
#             owner_id=zme.zuid,
#         )
#         for entry in entries
#     ]

#     zme.zdb.add_all(history_rows)
#     await zme.zdb.flush()

#     await zme.zdb.execute(
#         delete(PayrollEntry).where(PayrollEntry.biz_id == zme.zbid)
#     )

#     next_start, next_end = _advance_period(
#         frequency=schedule.frequency,
#         period_start=period_start,
#         period_end=period_end,
#     )
#     await _create_entries_for_schedule(
#         schedule,
#         zme,
#         period_start=next_start,
#         period_end=next_end,
#     )
#     await zme.zdb.flush()

#     summary = await _history_summary(
#         zme=zme,
#         schedule_id=schedule_id,
#         period_key=period_key,
#     )
#     if summary is None:
#         raise HTTPException(status_code=500, detail="Failed to finalize payroll history")
#     return summary


# def _advance_period(
#     frequency: str | None,
#     period_start: date,
#     period_end: date,
# ) -> tuple[date, date]:
#     freq = (frequency or "").lower()
#     if freq == "weekly":
#         delta = timedelta(days=7)
#         return period_start + delta, period_end + delta
#     if freq == "biweekly":
#         delta = timedelta(days=14)
#         return period_start + delta, period_end + delta
#     if freq == "monthly":
#         return _add_months(period_start, 1), _add_months(period_end, 1)
#     if freq == "quarterly":
#         return _add_months(period_start, 3), _add_months(period_end, 3)
#     if freq == "annually":
#         return _add_months(period_start, 12), _add_months(period_end, 12)
#     if freq == "semimonthly":
#         if period_start.day <= 15:
#             last_day = monthrange(period_start.year, period_start.month)[1]
#             return date(period_start.year, period_start.month, 16), date(period_start.year, period_start.month, last_day)
#         next_year, next_month = _next_month(period_start.year, period_start.month)
#         return date(next_year, next_month, 1), date(next_year, next_month, 15)

#     raise HTTPException(status_code=400, detail=f"Unsupported payroll frequency '{freq}' for period advance")


# def _addpay_dayvalue: date, months: int) -> date:
#     month_index = (value.month - 1) + months
#     year = value.year + (month_index // 12)
#     month = (month_index % 12) + 1
#     day = min(value.day, monthrange(year, month)[1])
#     return date(year, month, day)


# def _next_month(year: int, month: int) -> tuple[int, int]:
#     if month == 12:
#         return year + 1, 1
#     return year, month + 1




async def history_detail(
    zme: ZMeDataClass,
    period_key: str | None = None,
    history_id: UUID | None = None,
) -> HistoryDetailResponse:
    schedule_id: UUID | None = None
    if history_id is not None:
        history_result = await zme.zdb.execute(
            select(PayrollHistory).where(
                PayrollHistory.id == history_id,
                PayrollHistory.biz_id == zme.zbid,
            )
        )
        history_row = history_result.scalar_one_or_none()
        if history_row is None:
            raise HTTPException(status_code=404, detail="Payroll history not found")
        period_key = history_row.period_key
        schedule_id = history_row.schedule_id

    if not period_key:
        raise HTTPException(status_code=400, detail="period_key or id is required")

    summary = await _history_summary(
        zme=zme,
        period_key=period_key,
        schedule_id=schedule_id,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="Payroll history not found")

    entries_query = select(PayrollHistory).where(
        PayrollHistory.period_key == period_key,
        PayrollHistory.biz_id == zme.zbid,
    )
    if schedule_id is not None:
        entries_query = entries_query.where(PayrollHistory.schedule_id == schedule_id)
    entries_result = await zme.zdb.execute(entries_query)
    entries = entries_result.scalars().all()
    return HistoryDetailResponse(
        summary=summary,
        entries=[PayrollHistoryEntryResponse.model_validate(entry) for entry in entries],
    )


async def _history_summary(
    zme: ZMeDataClass,
    period_key: str,
    schedule_id: UUID | None = None,
) -> HistoryListRow | None:
    summary_query = (
        select(
            PayrollHistory.schedule_id,
            PayrollHistory.period_start,
            PayrollHistory.period_end,
            PayrollHistory.period_key,
            PayrollHistory.pay_date.label("pay_day"),
            func.sum(PayrollHistory.gross).label("total_gross"),
            func.sum(PayrollHistory.total_deduction).label("total_deduction"),
            func.sum(PayrollHistory.net).label("total_net"),
            func.count(PayrollHistory.employee_id).label("employee_count"),
            func.sum(
                case((PayrollHistory.excluded.is_(True), 1), else_=0)
            ).label("excluded_count"),
        )
        .where(
            PayrollHistory.period_key == period_key,
            PayrollHistory.biz_id == zme.zbid,
        )
        .group_by(
            PayrollHistory.schedule_id,
            PayrollHistory.period_start,
            PayrollHistory.period_end,
            PayrollHistory.period_key,
            PayrollHistory.pay_date,
        )
    )
    if schedule_id is not None:
        summary_query = summary_query.where(PayrollHistory.schedule_id == schedule_id)
    summary_result = await zme.zdb.execute(summary_query)
    row = summary_result.first()
    if not row:
        return None

    total_gross = _sum_or_zero(row.total_gross)
    total_deduction = _sum_or_zero(row.total_deduction)
    total_net = _sum_or_zero(row.total_net)

    return HistoryListRow(
        schedule_id=row.schedule_id,
        period_start=row.period_start,
        period_end=row.period_end,
        period_key=row.period_key,
        pay_day=row.pay_day,
        status="finalized",
        total_gross=total_gross,
        payroll_cost=total_gross,
        total_net=total_net,
        taxes_and_deductions=total_deduction,
        employee_count=int(row.employee_count or 0),
        excluded_count=int(row.excluded_count or 0),
    )
