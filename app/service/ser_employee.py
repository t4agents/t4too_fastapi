from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.t4.m_employee import EmployeeDB
from app.db.repo.repo_employee import (
    create_employee,
    get_employee_by_id,
    list_employees,
    update_employee_fields,
)


async def fetch_employees(sbu_client_id: UUID, db: AsyncSession) -> list[EmployeeDB]:
    return await list_employees(db, sbu_client_id)


async def create_or_update_employee(zuid: UUID, db: AsyncSession, payload: dict) -> EmployeeDB:

    
    base_ids = {
        "ten_id": zuid,
        "biz_id": zuid,
        "usr_id": zuid,
        "cli_id": zuid,
        "created_by": zuid,
    }
    employee_id = payload.get("id")
    updates = {k: v for k, v in payload.items() if k not in {"id", "full_name"}}
    if employee_id:
        existing = await get_employee_by_id(db, employee_id, zuid)
        if existing:
            return await update_employee_fields(db, existing, updates)
    data = {**base_ids, **updates}
    return await create_employee(db, data)
