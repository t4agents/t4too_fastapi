from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_employee import EmployeeDB
from app.db.repo.repo_utils import coerce_model_values


async def list_employees(db: AsyncSession, sbu_client_id: UUID) -> List[EmployeeDB]:
    result = await db.execute(
        select(EmployeeDB)
        .where(
            EmployeeDB.cli_id == sbu_client_id,
            # or_(EmployeeDB.is_deleted == False, EmployeeDB.is_deleted.is_(None)),
        )
        .order_by(EmployeeDB.created_at.desc())
    )
    return list(result.scalars().all())


async def get_employee_by_id(db: AsyncSession, employee_id: UUID, zjwt: JWType) -> Optional[EmployeeDB]:
    result = await db.execute(
        select(EmployeeDB)
        .where(EmployeeDB.id == employee_id, EmployeeDB.created_by == zjwt["zuid"])
    )
    return result.scalar_one_or_none()


async def create_employee(db: AsyncSession, payload: dict) -> EmployeeDB:
    employee = EmployeeDB(**coerce_model_values(EmployeeDB, payload))
    db.add(employee)
    await db.commit()
    # await db.refresh(employee)
    return employee


async def update_employee_fields(db: AsyncSession, employee: EmployeeDB, updates: dict) -> EmployeeDB:
    if updates:
        for key, value in coerce_model_values(employee, updates).items():
            setattr(employee, key, value)
        db.add(employee)
        await db.commit()
        # await db.refresh(employee)
    return employee
