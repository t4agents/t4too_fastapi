from typing import Any, List, Optional, Literal

from pydantic import BaseModel, Field


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)


class RagQueryResult(BaseModel):
    score: Optional[float] = None
    distance: Optional[float] = None
    embedding: dict[str, Any]
    history: dict[str, Any]


class RagQueryResponse(BaseModel):
    query: str
    top_k: int
    results: List[RagQueryResult]


class RagAnswerEvidence(BaseModel):
    evidence_id: int
    score: Optional[float] = None
    source_id: str
    chunk: str
    history: dict[str, Any]


class RagAnswerResponse(BaseModel):
    query: str
    top_k: int
    model: str
    answer: str
    confidence: float
    reasoning_summary: List[str]
    citations: List[int]
    limitations: str
    model_reasoning_summary: List[str]
    evidence: List[RagAnswerEvidence]


class RagRerankEvidence(BaseModel):
    evidence_id: int
    score: Optional[float] = None
    source_id: str
    chunk: str
    history: dict[str, Any]


class RagRerankAnswerResponse(BaseModel):
    query: str
    route: Optional[Literal["rag", "general", "sql"]] = None
    sql: Optional[str] = None
    top_k: int
    model: str
    rerank_model: str
    answer: str
    confidence: float
    reasoning_summary: List[str]
    citations: List[int]
    limitations: str
    model_reasoning_summary: List[str]
    evidence: List[RagRerankEvidence]
