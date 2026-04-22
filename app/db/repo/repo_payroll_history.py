from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_history import PayrollHistoryDB


async def list_payroll_history(db: AsyncSession, sbu_client_id: UUID) -> List[PayrollHistoryDB]:
    result = await db.execute(
        select(PayrollHistoryDB)
        .where(PayrollHistoryDB.cli_id == sbu_client_id)
        .order_by(PayrollHistoryDB.created_at.desc())
    )
    return list(result.scalars().all())
