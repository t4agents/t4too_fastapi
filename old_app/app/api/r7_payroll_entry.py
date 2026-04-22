from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import List, Optional

from app.core.dependency_injection import ZMeDataClass, get_zme_be_list
from app.schemas.sch_payroll_entry import (
    PayrollEntryAddEmployeesRequest,
    PayrollEntryResponse,
    PayrollEntryUpdate,
)
from app.service.ser7_payroll_entry import (
    list_current_entry_employees,
    add_entry_employees,
    edit_entry,
    finalize_entry,
)

entryRou = APIRouter()


@entryRou.get("/show_current_entry", response_model=List[PayrollEntryResponse],)
async def list_current_entrie_employees(skip: int = Query(0, ge=0),limit: int = Query(100, ge=1, le=1000),zme: ZMeDataClass = Depends(get_zme_be_list),):
    return await list_current_entry_employees(zme=zme,skip=skip,limit=limit,)


@entryRou.post("/edit", response_model=PayrollEntryResponse)
async def edit_payroll_entry(
    payload: PayrollEntryUpdate,
    zme: ZMeDataClass = Depends(get_zme_be_list),
):
    return await edit_entry(payload, zme)


@entryRou.post("/add_employees", response_model=List[PayrollEntryResponse])
async def add_employees_to_entry(
    payload: PayrollEntryAddEmployeesRequest,
    zme: ZMeDataClass = Depends(get_zme_be_list),
):
    return await add_entry_employees(payload, zme)




@entryRou.post("/finalize")
async def finalize_payroll_entries(zme: ZMeDataClass = Depends(get_zme_be_list),):
    return await finalize_entry(zme=zme,)


