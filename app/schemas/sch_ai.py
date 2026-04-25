from pydantic import BaseModel, Field

from typing import Any, List, Optional, Literal
from uuid import UUID


class JWType(BaseModel):
    zuid: UUID | None = None
    ztid: UUID | None = None
    zbid: UUID | None = None
    zcid: UUID | None = None
    zemail: str | None = None

    app_metadata: dict[str, Any] = Field(default_factory=dict)
    user_metadata: dict[str, Any] = Field(default_factory=dict)


class RagHit(BaseModel):
    evidence_id: int
    score: Optional[float] = None
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    source_id: str
    chunk: str
    history: dict[str, Any]


class RagRetrieveRes(BaseModel):
    query: str
    top_k: int
    mode: Literal["vector", "keyword", "hybrid"]
    results: List[RagHit]
