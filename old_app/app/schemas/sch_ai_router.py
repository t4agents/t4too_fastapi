from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.sch_ai_embedding import RagRerankAnswerResponse


class RouterQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1)


class GeneralAnswerResponse(BaseModel):
    query: str
    model: str
    answer: str
    confidence: float
    reasoning_summary: List[str]
    limitations: str
    model_reasoning_summary: List[str]


class RoutedAnswerResponse(BaseModel):
    query: str
    route: Literal["rag", "general"]
    route_confidence: float
    route_rationale: str
    route_model_reasoning_summary: List[str]
    rag: Optional[RagRerankAnswerResponse] = None
    general: Optional[GeneralAnswerResponse] = None
