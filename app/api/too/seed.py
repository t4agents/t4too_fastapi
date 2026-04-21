from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_async import get_db_rls
from app.schemas.sch_seed import SeedRefreshOut
from app.service.ser_seed import apply_seed_defaults

seedRou = APIRouter()


@seedRou.post("/seed/refresh", response_model=SeedRefreshOut)
async def post_seed_refresh(
    zuid: UUID = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    summary = await apply_seed_defaults(zuid, db, reset=False)
    return SeedRefreshOut(**summary)
