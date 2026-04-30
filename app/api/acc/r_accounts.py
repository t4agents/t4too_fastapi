from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import COADB
from app.schemas.sch_acc import AccountCreate, AccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountOut])
def list_accounts(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> list[Account]:
    return list(db.execute(select(Account).where(Account.owner_id == user.owner_id).order_by(Account.code.asc())).scalars().all())


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(
    payload: AccountCreate,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> Account:
    exists = db.execute(
        select(Account.id).where(and_(Account.owner_id == user.owner_id, Account.code == payload.code))
    ).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account code already exists")

    account = Account(owner_id=user.owner_id, **payload.model_dump())
    db.add(account)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create account") from exc
    db.refresh(account)
    return account

