from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_async import get_db_rls
from app.db.models.too.z_be import ZBizEntityDB
from app.service.ser_be import fetch_be_profile, update_be_profile
from app.service.ser_seed import apply_seed_defaults

beRou = APIRouter()


def _to_db_dict(be: ZBizEntityDB) -> dict[str, Any]:
    return {column.name: getattr(be, column.name) for column in be.__table__.columns}


@beRou.get("/getbe", response_model=dict)
async def get_be_profile(
    zjwt: dict[str, Any] = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    zuid = UUID(zjwt["zuid"])
    try:
        be = await fetch_be_profile(zuid, db)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
        await apply_seed_defaults(zuid, db, reset=False)
        be = await fetch_be_profile(zuid, db)
    return _to_db_dict(be)


@beRou.post("/savebe", response_model=dict)
async def post_be_profile(
    payload: dict[str, Any],
    zjwt: dict = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    updates = payload
    try:
        be = await update_be_profile(zuid, db, updates)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
        await apply_seed_defaults(zuid, db, reset=False)
        be = await update_be_profile(zuid, db, updates)
    return _to_db_dict(be)
