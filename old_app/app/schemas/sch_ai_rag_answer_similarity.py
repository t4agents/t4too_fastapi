from typing import Optional, List

from pydantic import BaseModel, Field


class RagEvalAnswerSimilarityRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG answer similarity run", min_length=1)
    include_rows: bool = True


class RagEvalAnswerSimilarityRow(BaseModel):
    run_id: str
    dataset_id: str
    question: str
    expected_answer: str
    answer: str
    answer_similarity: Optional[float] = None
    similarity_note: str
    top_k: int


class RagEvalAnswerSimilarityResponse(BaseModel):
    run_id: str
    description: str
    top_k: int
    total: int
    avg_answer_similarity: Optional[float] = None
    rows: Optional[List[RagEvalAnswerSimilarityRow]] = None
