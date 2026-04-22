from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_period import PayrollPeriodDB
from app.db.repo.repo_payroll_period import list_payroll_periods


async def fetch_payroll_periods(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollPeriodDB]:
    return await list_payroll_periods(db, sbu_client_id)
