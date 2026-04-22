from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB
from app.db.repo.repo_payroll_schedule import list_payroll_schedules


async def fetch_payroll_schedules(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollScheduleDB]:
    return await list_payroll_schedules(db, sbu_client_id)
