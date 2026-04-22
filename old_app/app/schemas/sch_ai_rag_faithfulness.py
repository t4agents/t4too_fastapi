from typing import Optional, List

from pydantic import BaseModel, Field


class RagEvalFaithfulnessRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG faithfulness run", min_length=1)
    judge: bool = False
    include_rows: bool = True


class RagEvalFaithfulnessRow(BaseModel):
    run_id: str
    dataset_id: str
    question: str
    answer: str
    retrieved_source_ids: List[str]
    citations: List[int]
    is_faithful: Optional[bool] = None
    top_k: int
    judge: str


class RagEvalFaithfulnessResponse(BaseModel):
    run_id: str
    description: str
    top_k: int
    total: int
    avg_faithfulness: Optional[float] = None
    rows: Optional[List[RagEvalFaithfulnessRow]] = None
