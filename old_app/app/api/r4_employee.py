from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import List

from app.core.dependency_injection import ZMeDataClass, get_zme

from app.schemas.sch_employee import (    EmployeeCreate,    EmployeeResponse,    EmployeeUpdate,    )
from app.service.ser4_employee import (    create_employee, list_employees, delete_employee, edit_employee)

employeeRou = APIRouter()


@employeeRou.get("/list", response_model=List[EmployeeResponse])
async def listEmployee(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    zme: ZMeDataClass = Depends(get_zme),
):
    """List all employees with pagination."""
    return await list_employees(skip=skip, limit=limit, zme=zme)


@employeeRou.post("/new", response_model=EmployeeResponse)
async def createEmployee(payload: EmployeeCreate,
    zme: ZMeDataClass = Depends(get_zme),
):
    return await create_employee(payload, zme)


@employeeRou.patch("/edit", response_model=EmployeeResponse)
async def patchEmployee(
    payload: EmployeeUpdate,
    zme: ZMeDataClass = Depends(get_zme),
):
    print(f"Received patch request for employee with data: {payload} and scope: {zme}")
    return await edit_employee(zme, payload)


@employeeRou.delete("/delete", )
async def delete(
    payload: EmployeeUpdate,
    zme: ZMeDataClass = Depends(get_zme),
):
    """Delete employee by ID."""
    return await delete_employee(payload, zme)



# @employeeRou.patch("/patchbyid/{employee_id}", response_model=EmployeeResponse)
# async def update(
#     employee_id: UUID,
#     data: EmployeeUpdate,
#     myscope: ZMe_DataClass = Depends(get_zme_be_list),
# ):
#     """Update employee by ID."""
#     return await update_employee(employee_id, data, myscope)




# @employeeRou.get("/getbyid/{employee_id}", response_model=EmployeeResponse)
# async def get(
#     employee_id: UUID,
#     myscope: ZMe_DataClass = Depends(get_zme_be_list),
# ):
#     """Get employee by ID."""
#     return await get_employee(employee_id, myscope)




# @employeeRou.get("/search/by-name", response_model=List[EmployeeResponse])
# async def search(
#     first_name: str = Query(..., min_length=1),
#     last_name: str = Query(..., min_length=1),
#     myscope: ZMe_DataClass = Depends(get_zme_be_list),
# ):
#     """Search employees by first and last name."""
#     return await search_employees(first_name, last_name, myscope)



# @employeeRou.get("/stats/count")
# async def count(
#     myscope: ZMe_DataClass = Depends(get_zme_be_list),
# ):
#     """Get total employee count."""
#     return await get_employee_count(myscope)


# @employeeRou.get("/form-options", response_model=EmployeeFormOptionsResponse)
# async def form_options(
#     myscope: ZMe_DataClass = Depends(get_zme_be_list),
# ):
#     """Get employee form dropdown options with default values."""
#     return await get_employee_form_options(myscope)
