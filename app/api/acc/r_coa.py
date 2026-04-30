from fastapi import APIRouter, Depends
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.deps import UserContext, get_current_user, get_db
from app.db.models.acc.ac_ledger import COADB
from app.services.coa_templates import generic_startup_template

router = APIRouter(prefix="/coa", tags=["coa"])


@router.get("/templates/generic")
def get_generic_template() -> dict[str, object]:
    accounts = generic_startup_template()
    return {
        "template": "generic_startup_ca",
        "seed_required": False,
        "accounts": accounts,
    }


@router.post("/templates/generic/apply")
def apply_generic_template(
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user),
) -> dict:
    created = 0
    existing = 0
    for item in generic_startup_template():
        found = db.execute(
            select(Account.id).where(and_(Account.owner_id == user.owner_id, Account.code == item["code"]))
        ).first()
        if found:
            existing += 1
            continue
        db.add(
            Account(
                owner_id=user.owner_id,
                code=item["code"],
                name=item["name"],
                type=item["type"],
            )
        )
        created += 1
    db.commit()
    return {"created": created, "existing": existing}
