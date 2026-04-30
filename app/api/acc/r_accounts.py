from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import COADB
from app.schemas.sch_acc import AccountCreate, AccountOut, AccountType
from app.schemas.sch_ai import JWType

router = APIRouter(prefix="/accounts", tags=["accounts"])

_ACCOUNT_TYPES: set[str] = {"asset", "liability", "equity", "revenue", "expense"}


def _to_account_out(row: COADB) -> AccountOut:
    if row.type not in _ACCOUNT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid account type: {row.type}")
    return AccountOut(
        id=row.id,
        code=row.code,
        name=row.name,
        type=cast(AccountType, row.type),
        subtype=row.subtype,
        is_active=not bool(row.is_deleted),
    )


@router.get("", response_model=list[AccountOut])
async def list_accounts(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> list[AccountOut]:
    rows = (await db.execute(select(COADB).order_by(COADB.code.asc()))).scalars().all()
    return [_to_account_out(row) for row in rows]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> AccountOut:
    exists = (await db.execute(select(COADB.id).where(COADB.code == payload.code))).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")

    account = COADB(
        ten_id=zjwt.ztid,
        biz_id=zjwt.zbid,
        cli_id=zjwt.zcid,
        usr_id=zjwt.zuid,
        created_by=zjwt.zuid,
        **payload.model_dump(),
    )
    db.add(account)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create account") from exc
    await db.refresh(account)
    return _to_account_out(account)
