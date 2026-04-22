from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_entry import PayrollEntryDB


async def list_payroll_entries(db: AsyncSession, sbu_client_id: UUID) -> List[PayrollEntryDB]:
    result = await db.execute(
        select(PayrollEntryDB)
        .where(PayrollEntryDB.cli_id == sbu_client_id)
        .order_by(PayrollEntryDB.created_at.desc())
    )
    return list(result.scalars().all())
