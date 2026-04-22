from typing import Optional, List

from pydantic import BaseModel, Field


class RagEvalAnswerRelevanceRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG answer relevance run", min_length=1)
    include_rows: bool = True


class RagEvalAnswerRelevanceRow(BaseModel):
    run_id: str
    dataset_id: str
    question: str
    expected_answer: str
    answer: str
    is_relevant: Optional[bool] = None
    relevance_note: str
    top_k: int


class RagEvalAnswerRelevanceResponse(BaseModel):
    run_id: str
    description: str
    top_k: int
    total: int
    avg_answer_relevance: Optional[float] = None
    rows: Optional[List[RagEvalAnswerRelevanceRow]] = None
