from typing import Optional, List

from pydantic import BaseModel, Field


class RagEvalRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG eval run", min_length=1)
    judge: bool = False
    no_evidence: bool = False
    evidence_max_chars: int = Field(default=500, ge=50)
    no_relevancy: bool = False
    include_rows: bool = True
    include_failures: bool = False


class RagEvalRow(BaseModel):
    run_id: str
    dataset_id: str
    question: str
    expected_answer: str
    answer: str
    recall_at_k: float
    precision_at_k: float
    is_faithful: Optional[bool] = None
    answer_relevancy: Optional[float] = None
    route: Optional[str] = None
    model: Optional[str] = None
    rerank_model: Optional[str] = None
    top_k: int


class RagEvalResponse(BaseModel):
    run_id: str
    description: str
    top_k: int
    total: int
    failures: int
    avg_recall_at_k: Optional[float] = None
    avg_precision_at_k: Optional[float] = None
    avg_faithfulness: Optional[float] = None
    avg_answer_relevancy: Optional[float] = None
    rows: Optional[List[RagEvalRow]] = None
    failure_rows: Optional[List[RagEvalRow]] = None
