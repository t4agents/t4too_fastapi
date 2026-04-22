import asyncio
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.db_async import T4DbSession
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.db.seeds.data_payroll_schedules import (
    SEED_PAYROLL_SCHEDULES,
    TEMPLATE_PAYROLL_SCHEDULES,
)


async def seed_payroll_schedules(*, overwrite: bool = False) -> None:
    async with T4DbSession() as session:
        async with session.begin():
            for row in SEED_PAYROLL_SCHEDULES:
                existing = await session.scalar(
                    select(PayrollSchedule).where(PayrollSchedule.id == row["id"])
                )
                if existing:
                    if overwrite:
                        for key, value in row.items():
                            setattr(existing, key, value)
                        session.add(existing)
                    continue
                session.add(PayrollSchedule(**row))


def build_payroll_schedule_rows(
    *,
    ten_id: UUID,
    biz_id: UUID,
    owner_id: UUID,
    created_by: UUID | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for template in TEMPLATE_PAYROLL_SCHEDULES:
        row = dict(template)
        row.update(
            {
                "id": uuid4(),
                "ten_id": ten_id,
                "biz_id": biz_id,
                "owner_id": owner_id,
                "created_by": created_by,
            }
        )
        rows.append(row)
    return rows


async def ensure_payroll_schedules_for_be(
    session: AsyncSession,
    *,
    ten_id: UUID,
    biz_id: UUID,
    owner_id: UUID,
    created_by: UUID | None = None,
) -> None:
    rows = build_payroll_schedule_rows(
        ten_id=ten_id,
        biz_id=biz_id,
        owner_id=owner_id,
        created_by=created_by,
    )
    for row in rows:
        existing_id = await session.scalar(
            select(PayrollSchedule.id).where(
                PayrollSchedule.biz_id == biz_id,
                PayrollSchedule.frequency == row["frequency"],
            )
        )
        if existing_id:
            continue
        session.add(PayrollSchedule(**row))


def main() -> None:
    asyncio.run(seed_payroll_schedules())


if __name__ == "__main__":
    main()
