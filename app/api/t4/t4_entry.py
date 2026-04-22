from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.t4.m_payroll_entry import PayrollEntryDB
from app.schemas.sch_payroll_entry import PayrollEntryOut
from app.service.ser_payroll_entry import fetch_payroll_entries

entryRou = APIRouter()


def _to_db_dict(payroll_entry: PayrollEntryDB) -> dict[str, Any]:
    return {
        column.name: getattr(payroll_entry, column.name)
        for column in payroll_entry.__table__.columns
    }


@entryRou.get("/get_payroll_entry_list", response_model=list[PayrollEntryOut])
async def get_payroll_entry_list(
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    sbu_client_id = zjwt["user_metadata"]["sbu_client_id"]
    entries = await fetch_payroll_entries(sbu_client_id, db)
    return [PayrollEntryOut(**_to_db_dict(entry)) for entry in entries]
