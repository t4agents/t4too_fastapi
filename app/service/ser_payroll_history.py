from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import case, func, select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_history import PayrollHistoryDB
from app.db.repo.repo_payroll_history import list_payroll_history
from app.schemas.sch_payroll_history import (
    PayrollHistoryDetailEntryOut,
    PayrollHistoryDetailOut,
    PayrollHistorySummaryOut,
)


async def fetch_payroll_history(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollHistoryDB]:
    return await list_payroll_history(db, sbu_client_id)


async def fetch_payroll_history_summary_list(
    sbu_client_id: UUID,
    db: AsyncSession,
) -> list[PayrollHistorySummaryOut]:
    query = (
        select(
            PayrollHistoryDB.schedule_id,
            PayrollHistoryDB.period_start,
            PayrollHistoryDB.period_end,
            PayrollHistoryDB.period_key,
            PayrollHistoryDB.pay_date.label("pay_day"),
            func.sum(PayrollHistoryDB.gross).label("total_gross"),
            func.sum(PayrollHistoryDB.total_deduction).label("total_deduction"),
            func.sum(PayrollHistoryDB.net).label("total_net"),
            func.count(PayrollHistoryDB.employee_id).label("employee_count"),
            func.sum(case((PayrollHistoryDB.excluded.is_(True), 1), else_=0)).label("excluded_count"),
        )
        .where(PayrollHistoryDB.cli_id == sbu_client_id)
        .group_by(
            PayrollHistoryDB.schedule_id,
            PayrollHistoryDB.period_start,
            PayrollHistoryDB.period_end,
            PayrollHistoryDB.period_key,
            PayrollHistoryDB.pay_date,
        )
        .order_by(PayrollHistoryDB.period_end.desc())
    )
    result = await db.execute(query)
    rows = result.all()

    return [
        PayrollHistorySummaryOut(
            schedule_id=row.schedule_id,
            period_start=row.period_start,
            period_end=row.period_end,
            period_key=row.period_key,
            pay_day=row.pay_day,
            status="finalized",
            total_gross=_sum_or_zero(row.total_gross),
            payroll_cost=_sum_or_zero(row.total_gross),
            total_net=_sum_or_zero(row.total_net),
            taxes_and_deductions=_sum_or_zero(row.total_deduction),
            employee_count=int(row.employee_count or 0),
            excluded_count=int(row.excluded_count or 0),
        )
        for row in rows
    ]


async def fetch_payroll_history_detail(
    sbu_client_id: UUID,
    db: AsyncSession,
    *,
    period_key: str | None = None,
    history_id: UUID | None = None,
) -> PayrollHistoryDetailOut:
    schedule_id: UUID | None = None
    if history_id is not None:
        result = await db.execute(
            select(PayrollHistoryDB).where(
                PayrollHistoryDB.id == history_id,
                PayrollHistoryDB.cli_id == sbu_client_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Payroll history not found")
        period_key = row.period_key
        schedule_id = row.schedule_id

    if not period_key:
        raise HTTPException(status_code=400, detail="period_key or id is required")

    summary = await _history_summary(
        sbu_client_id=sbu_client_id,
        db=db,
        period_key=period_key,
        schedule_id=schedule_id,
    )
    if summary is None:
        raise HTTPException(status_code=404, detail="Payroll history not found")

    entries_query = select(PayrollHistoryDB).where(
        PayrollHistoryDB.period_key == period_key,
        PayrollHistoryDB.cli_id == sbu_client_id,
    )
    if schedule_id is not None:
        entries_query = entries_query.where(PayrollHistoryDB.schedule_id == schedule_id)
    entries_result = await db.execute(entries_query.order_by(PayrollHistoryDB.created_at.asc()))
    entries = list(entries_result.scalars().all())
    return PayrollHistoryDetailOut(
        summary=summary,
        entries=[
            PayrollHistoryDetailEntryOut(
                id=entry.id,
                schedule_id=entry.schedule_id,
                payroll_period_id=entry.payroll_period_id,
                employee_id=entry.employee_id,
                period_key=entry.period_key,
                full_name=entry.full_name,
                employment_type=entry.employment_type,
                annual_salary_snapshot=entry.annual_salary_snapshot,
                hourly_rate_snapshot=entry.hourly_rate_snapshot,
                regular_hours=entry.regular_hours,
                overtime_hours=entry.overtime_hours,
                bonus=entry.bonus,
                vacation=entry.vacation,
                adjustment=entry.adjustment,
                cpp=entry.cpp,
                ei=entry.ei,
                tax=entry.tax,
                gross=entry.gross,
                total_deduction=entry.total_deduction,
                net=entry.net,
                excluded=entry.excluded,
                status=entry.status,
            )
            for entry in entries
        ],
    )


async def _history_summary(
    sbu_client_id: UUID,
    db: AsyncSession,
    *,
    period_key: str,
    schedule_id: UUID | None = None,
) -> PayrollHistorySummaryOut | None:
    query = (
        select(
            PayrollHistoryDB.schedule_id,
            PayrollHistoryDB.period_start,
            PayrollHistoryDB.period_end,
            PayrollHistoryDB.period_key,
            PayrollHistoryDB.pay_date.label("pay_day"),
            func.sum(PayrollHistoryDB.gross).label("total_gross"),
            func.sum(PayrollHistoryDB.total_deduction).label("total_deduction"),
            func.sum(PayrollHistoryDB.net).label("total_net"),
            func.count(PayrollHistoryDB.employee_id).label("employee_count"),
            func.sum(case((PayrollHistoryDB.excluded.is_(True), 1), else_=0)).label("excluded_count"),
        )
        .where(
            PayrollHistoryDB.period_key == period_key,
            PayrollHistoryDB.cli_id == sbu_client_id,
        )
        .group_by(
            PayrollHistoryDB.schedule_id,
            PayrollHistoryDB.period_start,
            PayrollHistoryDB.period_end,
            PayrollHistoryDB.period_key,
            PayrollHistoryDB.pay_date,
        )
    )
    if schedule_id is not None:
        query = query.where(PayrollHistoryDB.schedule_id == schedule_id)

    result = await db.execute(query)
    row = result.first()
    if not row:
        return None

    return PayrollHistorySummaryOut(
        schedule_id=row.schedule_id,
        period_start=row.period_start,
        period_end=row.period_end,
        period_key=row.period_key,
        pay_day=row.pay_day,
        status="finalized",
        total_gross=_sum_or_zero(row.total_gross),
        payroll_cost=_sum_or_zero(row.total_gross),
        total_net=_sum_or_zero(row.total_net),
        taxes_and_deductions=_sum_or_zero(row.total_deduction),
        employee_count=int(row.employee_count or 0),
        excluded_count=int(row.excluded_count or 0),
    )


def _sum_or_zero(value: Decimal | None) -> Decimal:
    return value if value is not None else Decimal("0.00")
