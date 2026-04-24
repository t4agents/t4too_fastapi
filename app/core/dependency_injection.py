from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.sch_ai import JWType


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


def build_zme(zjwt: JWType, db: AsyncSession) -> ZMeDataClass:
    cli_id = zjwt.zcid or zjwt.zuid
    if cli_id is None:
        raise HTTPException(status_code=400, detail="Missing client/user id in JWT context.")
    return ZMeDataClass(
        ztid=zjwt.ztid,
        zbid=zjwt.zbid,
        zuid=zjwt.zuid,
        zdb=db,
        cli_id=cli_id,
    )
