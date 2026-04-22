from datetime import date
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from fastapi import HTTPException

from app.core.dependency_injection import ZMeDataClass
from app.db.models.m_employee import Employee
from app.db.models.m_payroll_schedule import PayrollSchedule
from app.db.repo.repo_employee import EmployeeRepository
from app.schemas.sch_employee import (
    EmployeeCreate,
    EmployeeFormOptionsResponse,
    EmployeePayrollScheduleOption,
    EmployeeUpdate, EmployeeResponse
)


async def list_employees(zme: ZMeDataClass, skip: int = 0, limit: int = 100) -> List[EmployeeResponse]:
    query = select(Employee).where(
        Employee.is_deleted != True,
        Employee.biz_id == zme.zbid,
    ).order_by(Employee.first_name.desc()).offset(skip).limit(limit)

    result = await zme.zdb.execute(query)
    employees = result.scalars().all()

    return [EmployeeResponse.model_validate(emp, from_attributes=True) for emp in employees]




async def create_employee(payload: EmployeeCreate, zme: ZMeDataClass) -> Employee:
    employee_data = payload.model_dump(exclude_none=True)
    
    for immutable_key in ("biz_id", "ten_id", "owner_id"):employee_data.pop(immutable_key, None)
    
    employee_data["biz_id"] = zme.zbid
    employee_data["ten_id"] = zme.ztid
    employee_data["owner_id"] = zme.zuid

    employee = Employee(**employee_data)
    
    zme.zdb.add(employee)
    await zme.zdb.flush()
    await zme.zdb.refresh(employee)
    return employee


async def edit_employee(zme: ZMeDataClass, payload: EmployeeUpdate) -> Employee:
    result = await zme.zdb.execute(select(Employee).where(Employee.id == payload.id))
    employee = result.scalars().first()
    if not employee:raise HTTPException(status_code=404, detail="Employee not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items(): setattr(employee, field, value)

    zme.zdb.add(employee)
    await zme.zdb.flush()
    await zme.zdb.refresh(employee)
    return employee


async def delete_employee(payload: EmployeeUpdate, zme: ZMeDataClass) -> dict:
    if not payload.id:
        raise HTTPException(status_code=400, detail="Employee id is required")

    result = await zme.zdb.execute(
        select(Employee).where(
            Employee.id == payload.id,
            Employee.biz_id == zme.zbid,
        )
    )
    employee = result.scalars().first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    await zme.zdb.delete(employee)
    await zme.zdb.flush()
    return {"detail": "Employee deleted successfully"}



