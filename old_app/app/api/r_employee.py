from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.db.db_async import get_db
from app.schemas.sch_employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.service.ser_employee import (
    create_employee,
    get_employee,
    list_employees,
    search_employees,
    update_employee,
    delete_employee,
    get_employee_count,
)

employeeRou = APIRouter()


@employeeRou.post("", response_model=EmployeeResponse)
async def create(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new employee."""
    return await create_employee(data, db)


@employeeRou.get("/{employee_id}", response_model=EmployeeResponse)
async def get(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get employee by ID."""
    return await get_employee(employee_id, db)


@employeeRou.get("", response_model=List[EmployeeResponse])
async def list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """List all employees with pagination."""
    return await list_employees(db, skip=skip, limit=limit)


@employeeRou.get("/search/by-name", response_model=List[EmployeeResponse])
async def search(
    first_name: str = Query(..., min_length=1),
    last_name: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Search employees by first and last name."""
    return await search_employees(first_name, last_name, db)


@employeeRou.patch("/{employee_id}", response_model=EmployeeResponse)
async def update(
    employee_id: UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update employee by ID."""
    return await update_employee(employee_id, data, db)


@employeeRou.delete("/{employee_id}")
async def delete(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete employee by ID."""
    return await delete_employee(employee_id, db)


@employeeRou.get("/stats/count")
async def count(
    db: AsyncSession = Depends(get_db),
):
    """Get total employee count."""
    return await get_employee_count(db)
