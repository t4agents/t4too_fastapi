from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.db.models.acc.ac_ledger import COADB
from app.schemas.sch_ai import JWType
from app.service.acc.coa_templates import generic_startup_template

router = APIRouter(prefix="/coa", tags=["coa"])


@router.get("/templates/generic")
async def get_generic_template() -> dict[str, object]:
    accounts = generic_startup_template()
    return {"template": "generic_startup_ca", "seed_required": False, "accounts": accounts}


@router.post("/templates/generic/apply")
async def apply_generic_template(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> dict:
    created = 0
    existing = 0
    for item in generic_startup_template():
        found = (await db.execute(select(COADB.id).where(COADB.code == item["code"]))).first()
        if found:
            existing += 1
            continue
        db.add(
            COADB(
                ten_id=zjwt.ztid,
                biz_id=zjwt.zbid,
                cli_id=zjwt.zcid,
                usr_id=zjwt.zuid,
                created_by=zjwt.zuid,
                code=item["code"],
                name=item["name"],
                type=item["type"],
            )
        )
        created += 1
    await db.commit()
    return {"created": created, "existing": existing}
