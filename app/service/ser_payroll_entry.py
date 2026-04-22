from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_payroll_entry import PayrollEntryDB
from app.db.repo.repo_payroll_entry import list_payroll_entries


async def fetch_payroll_entries(sbu_client_id: UUID, db: AsyncSession) -> list[PayrollEntryDB]:
    return await list_payroll_entries(db, sbu_client_id)
