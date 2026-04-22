from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependency_injection import ZMeDataClass, get_zme_be_list
from app.schemas.sch_payroll_history import HistoryDetailResponse, HistoryListRow
from app.service.ser6_payroll_history import history_detail, list_history


historyRou = APIRouter()



@historyRou.get("/list", response_model=List[HistoryListRow])
async def list_payroll_history(zme: ZMeDataClass = Depends(get_zme_be_list),):
    return await list_history(zme=zme)


@historyRou.get("/detail", response_model=HistoryDetailResponse)
async def get_payroll_history_detail(
    id: Optional[str] = Query(default=None),
    period_key: Optional[str] = Query(default=None),
    zme: ZMeDataClass = Depends(get_zme_be_list),
):
    history_id: UUID | None = None
    if id and not period_key:
        try:
            history_id = UUID(id)
        except ValueError:
            period_key = id
    return await history_detail(
        zme=zme,
        history_id=history_id,
        period_key=period_key,
    )
