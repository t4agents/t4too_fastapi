from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.m_payroll_entry import PayrollEntry
from app.db.models.m_payroll_period import PayrollPeriod


class PayrollEntryRepository:
    def __init__(self, db: AsyncSession, active_biz_id: UUID):
        self.db = db
        self.active_biz_id = active_biz_id

    async def get_by_id(self, entry_id: UUID) -> Optional[PayrollEntry]:
        query = select(PayrollEntry).where(
            PayrollEntry.id == entry_id,
            PayrollEntry.biz_id == self.active_biz_id,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list_all(
        self,
        period_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PayrollEntry]:
        query = select(PayrollEntry).where(
            PayrollEntry.biz_id == self.active_biz_id
        )
        if period_id:
            query = query.join(PayrollPeriod, PayrollPeriod.id == PayrollEntry.payroll_period_id).where(
                PayrollEntry.payroll_period_id == period_id,
                PayrollPeriod.biz_id == self.active_biz_id,
            )

        result = await self.db.execute(query.offset(skip).limit(limit))
        return list(result.scalars().all())

    async def refresh(self, entry: PayrollEntry) -> PayrollEntry:
        await self.db.refresh(entry)
        return entry
