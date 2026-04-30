from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import PeriodCloseDB
from app.schemas.sch_ai import JWType

router = APIRouter(prefix="/periods", tags=["periods"])


@router.post("/{period_yyyymm}/close")
async def close_period(
    period_yyyymm: int,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> dict:
    row = (await db.execute(select(PeriodCloseDB).where(PeriodCloseDB.period_yyyymm == period_yyyymm))).scalar_one_or_none()
    if row and row.is_closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period already closed")
    if not row:
        row = PeriodCloseDB(
            ten_id=zjwt.ztid,
            biz_id=zjwt.zbid,
            cli_id=zjwt.zcid,
            usr_id=zjwt.zuid,
            created_by=zjwt.zuid,
            period_yyyymm=period_yyyymm,
        )
        db.add(row)
    row.is_closed = True
    row.closed_at = datetime.now(timezone.utc)
    row.closed_by = zjwt.zuid
    await db.commit()
    return {"period_yyyymm": period_yyyymm, "is_closed": True}


@router.post("/{period_yyyymm}/reopen")
async def reopen_period(
    period_yyyymm: int,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> dict:
    row = (await db.execute(select(PeriodCloseDB).where(PeriodCloseDB.period_yyyymm == period_yyyymm))).scalar_one_or_none()
    if not row:
        row = PeriodCloseDB(
            ten_id=zjwt.ztid,
            biz_id=zjwt.zbid,
            cli_id=zjwt.zcid,
            usr_id=zjwt.zuid,
            created_by=zjwt.zuid,
            period_yyyymm=period_yyyymm,
            is_closed=False,
        )
        db.add(row)
    row.is_closed = False
    row.closed_at = None
    row.closed_by = None
    await db.commit()
    return {"period_yyyymm": period_yyyymm, "is_closed": False}
