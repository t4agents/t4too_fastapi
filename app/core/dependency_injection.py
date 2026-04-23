from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
# from app.service.ser_ai_context import ai_context_from_zjwt


@dataclass(slots=True)
class ZMeDataClass:
    ztid: UUID | None
    zbid: UUID | None
    zuid: UUID | None
    zdb: AsyncSession
    cli_id: UUID

    @property
    def ten_id(self) -> UUID | None:
        return self.ztid

    @property
    def biz_id(self) -> UUID | None:
        return self.zbid

    @property
    def user_id(self) -> UUID | None:
        return self.zuid

    @property
    def db(self) -> AsyncSession:
        return self.zdb


async def get_zme(
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
) -> ZMeDataClass:
    ctx = ai_context_from_zjwt(zjwt, db)
    return ZMeDataClass(
        ztid=ctx.ten_id,
        zbid=ctx.biz_id,
        zuid=ctx.user_id,
        zdb=ctx.db,
        cli_id=ctx.cli_id,
    )
