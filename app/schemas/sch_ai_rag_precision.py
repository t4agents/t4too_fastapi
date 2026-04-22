from typing import Optional, List

from pydantic import BaseModel, Field


class RagEvalPrecisionRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG precision@k run", min_length=1)
    include_rows: bool = True


class RagEvalPrecisionRow(BaseModel):
    run_id: str
    dataset_id: str
    question: str
    expected_source_ids: List[str]
    retrieved_source_ids: List[str]
    precision_at_k: float
    top_k: int


class RagEvalPrecisionResponse(BaseModel):
    run_id: str
    description: str
    top_k: int
    total: int
    avg_precision_at_k: Optional[float] = None
    rows: Optional[List[RagEvalPrecisionRow]] = None
