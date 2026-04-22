from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_schedule import PayrollScheduleDB


async def list_payroll_schedules(db: AsyncSession, sbu_client_id: UUID) -> List[PayrollScheduleDB]:
    result = await db.execute(
        select(PayrollScheduleDB)
        .where(PayrollScheduleDB.cli_id == sbu_client_id)
        .order_by(PayrollScheduleDB.created_at.desc())
    )
    return list(result.scalars().all())
