from pydantic import BaseModel, Field

from typing import Any, List, Optional, Literal
from uuid import UUID


class JWType(BaseModel):
    ztid: UUID | None = None
    zbid: UUID | None = None
    zcid: UUID | None = None
    zuid: UUID | None = None

    app_metadata: dict[str, Any] = Field(default_factory=dict)
    user_metadata: dict[str, Any] = Field(default_factory=dict)