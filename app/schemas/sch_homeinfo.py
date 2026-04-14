from typing import Optional

from pydantic import BaseModel

from app.schemas.sch_userprofile import UserProfileOut


class HomeBizOut(BaseModel):
    be_name: Optional[str] = None


class HomeInfoOut(BaseModel):
    user: UserProfileOut
    biz: HomeBizOut

