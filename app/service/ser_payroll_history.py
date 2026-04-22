from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_history import PayrollHistoryDB
from app.db.repo.repo_payroll_history import list_payroll_history


async def fetch_payroll_history(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollHistoryDB]:
    return await list_payroll_history(db, sbu_client_id)
