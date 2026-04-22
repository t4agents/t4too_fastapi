from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_period import PayrollPeriodDB


async def list_payroll_periods(db: AsyncSession, sbu_client_id: UUID) -> List[PayrollPeriodDB]:
    result = await db.execute(
        select(PayrollPeriodDB)
        .where(PayrollPeriodDB.cli_id == sbu_client_id)
        .order_by(PayrollPeriodDB.created_at.desc())
    )
    return list(result.scalars().all())
