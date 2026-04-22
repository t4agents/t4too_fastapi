from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.t4.m_payroll_entry import PayrollEntryDB
from app.schemas.sch_payroll_entry import (
    PayrollEntryAddEmployeesRequest,
    PayrollEntryOut,
    PayrollEntryUpdate,
    PayrollFinalizeOut,
)
from app.service.ser_payroll_entry import (
    add_entry_employees,
    edit_payroll_entry,
    fetch_payroll_entries,
    finalize_payroll_entries,
)

entryRou = APIRouter()


def _to_db_dict(payroll_entry: PayrollEntryDB) -> dict[str, Any]:
    return {
        column.name: getattr(payroll_entry, column.name)
        for column in payroll_entry.__table__.columns
    }


@entryRou.get("/get_payroll_entry_list", response_model=list[PayrollEntryOut])
async def get_payroll_entry_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    sbu_client_id = zjwt["user_metadata"]["sbu_client_id"]
    entries = await fetch_payroll_entries(sbu_client_id, db)
    return [PayrollEntryOut(**_to_db_dict(entry)) for entry in entries[skip : skip + limit]]


@entryRou.post("/post_payroll_entry_edit", response_model=PayrollEntryOut)
async def post_payroll_entry_edit(
    payload: PayrollEntryUpdate,
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    entry = await edit_payroll_entry(payload, zjwt, db)
    return PayrollEntryOut(**_to_db_dict(entry))


@entryRou.post("/post_payroll_entry_add_employees", response_model=list[PayrollEntryOut])
async def post_payroll_entry_add_employees(
    payload: PayrollEntryAddEmployeesRequest,
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    entries = await add_entry_employees(payload, zjwt, db)
    return [PayrollEntryOut(**_to_db_dict(entry)) for entry in entries]


@entryRou.post("/post_payroll_entry_finalize", response_model=PayrollFinalizeOut)
async def post_payroll_entry_finalize(
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    out = await finalize_payroll_entries(zjwt, db)
    return PayrollFinalizeOut(**out)
