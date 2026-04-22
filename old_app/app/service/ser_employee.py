from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.db.models.m_employee import Employee
from app.db.models.m_payroll import PayrollSchedule
from app.db.repo.repo_employee import EmployeeRepository
from app.schemas.sch_employee import EmployeeCreate, EmployeeUpdate


async def create_employee(data: EmployeeCreate, db: AsyncSession) -> Employee:
    """Create a new employee."""
    repo = EmployeeRepository(db)

    # Check if employee with same SIN already exists
    existing = await repo.get_by_sin(data.sin)
    if existing:
        raise HTTPException(
            status_code=400, detail="Employee with this SIN already exists"
        )

    # Check if email already exists (if provided)
    if data.email:
        existing_email = await repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=400, detail="Employee with this email already exists"
            )

    # Validate payroll schedule exists
    schedule_result = await db.execute(
        select(PayrollSchedule).where(PayrollSchedule.id == data.payroll_schedule_id)
    )
    schedule = schedule_result.scalars().first()
    if not schedule:
        raise HTTPException(
            status_code=404, detail="Payroll schedule not found"
        )

    employee = Employee(**data.model_dump())
    return await repo.create(employee)


async def get_employee(employee_id: UUID, db: AsyncSession) -> Employee:
    """Get employee by ID."""
    repo = EmployeeRepository(db)
    employee = await repo.get_by_id(employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee


async def list_employees(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Employee]:
    """List all employees with pagination."""
    repo = EmployeeRepository(db)
    return await repo.list_all(skip=skip, limit=limit)


async def search_employees(
    first_name: str, last_name: str, db: AsyncSession
) -> List[Employee]:
    """Search employees by name."""
    repo = EmployeeRepository(db)
    employees = await repo.get_by_name(first_name, last_name)

    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")

    return employees


async def update_employee(
    employee_id: UUID, data: EmployeeUpdate, db: AsyncSession
) -> Employee:
    """Update employee by ID."""
    repo = EmployeeRepository(db)
    employee = await repo.get_by_id(employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check email uniqueness if being updated
    if data.email and data.email != employee.email:
        existing_email = await repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=400, detail="Email already in use by another employee"
            )
    # Validate payroll schedule exists if being updated
    if data.payroll_schedule_id:
        schedule_result = await db.execute(
            select(PayrollSchedule).where(PayrollSchedule.id == data.payroll_schedule_id)
        )
        schedule = schedule_result.scalars().first()
        if not schedule:
            raise HTTPException(
                status_code=404, detail="Payroll schedule not found"
            )
    update_data = data.model_dump(exclude_unset=True)
    return await repo.update(employee_id, update_data)


async def delete_employee(employee_id: UUID, db: AsyncSession) -> dict:
    """Soft delete employee by ID (sets is_deleted flag)."""
    repo = EmployeeRepository(db)
    employee = await repo.get_by_id(employee_id)

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    success = await repo.delete(employee_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete employee")

    return {"message": "Employee soft deleted successfully", "id": employee_id}


async def get_employee_count(db: AsyncSession) -> dict:
    """Get total employee count."""
    repo = EmployeeRepository(db)
    count = await repo.count()
    return {"total": count}
