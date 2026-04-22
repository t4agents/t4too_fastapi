from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.t4.m_payroll_history import PayrollHistoryDB
from app.schemas.sch_payroll_history import PayrollHistoryOut
from app.service.ser_payroll_history import fetch_payroll_history

historyRou = APIRouter()


def _to_db_dict(payroll_history: PayrollHistoryDB) -> dict[str, Any]:
    return {
        column.name: getattr(payroll_history, column.name)
        for column in payroll_history.__table__.columns
    }


@historyRou.get("/get_payroll_history_list", response_model=list[PayrollHistoryOut])
async def get_payroll_history_list(
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    sbu_client_id = zjwt["user_metadata"]["sbu_client_id"]
    history_rows = await fetch_payroll_history(sbu_client_id, db)
    return [PayrollHistoryOut(**_to_db_dict(history)) for history in history_rows]
