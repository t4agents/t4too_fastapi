from alembic.environment import List
from pydantic import BaseModel, Field
from uuid import UUID

from app.schemas.sch_be import BizEntityResponse

class ZMeBase(BaseModel):
    ztid: UUID
    zuid: UUID      
    zbid: UUID  # active biz id

    model_config = {
        "arbitrary_types_allowed": True,  # allows AsyncSession if needed
        "frozen": True,
        "from_attributes": True,
    }



# Full ZBeList model (matches ZBeList_DataClass)
class ZBeList(ZMeBase):
    zbe_list: List[BizEntityResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        **ZMeBase.model_config,  # inherit base config
    }

