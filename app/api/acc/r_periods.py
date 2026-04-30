from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import PeriodClose

router = APIRouter(prefix="/periods", tags=["periods"])


@router.post("/{period_yyyymm}/close")
def close_period(
    period_yyyymm: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    row = db.execute(
        select(PeriodClose).where(and_(PeriodClose.owner_id == user.owner_id, PeriodClose.period_yyyymm == period_yyyymm))
    ).scalar_one_or_none()
    if row and row.is_closed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Period already closed")
    if not row:
        row = PeriodClose(owner_id=user.owner_id, period_yyyymm=period_yyyymm)
        db.add(row)
    row.is_closed = True
    row.closed_at = datetime.now(timezone.utc)
    row.closed_by = user.user_id
    db.commit()
    return {"period_yyyymm": period_yyyymm, "is_closed": True}


@router.post("/{period_yyyymm}/reopen")
def reopen_period(
    period_yyyymm: int,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    row = db.execute(
        select(PeriodClose).where(and_(PeriodClose.owner_id == user.owner_id, PeriodClose.period_yyyymm == period_yyyymm))
    ).scalar_one_or_none()
    if not row:
        row = PeriodClose(owner_id=user.owner_id, period_yyyymm=period_yyyymm, is_closed=False)
        db.add(row)
    row.is_closed = False
    row.closed_at = None
    row.closed_by = None
    db.commit()
    return {"period_yyyymm": period_yyyymm, "is_closed": False}

