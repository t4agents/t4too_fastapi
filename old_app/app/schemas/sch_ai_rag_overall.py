from typing import Optional, Dict

from pydantic import BaseModel, Field


class RagEvalOverallRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG overall score run", min_length=1)
    judge: bool = False
    recall_weight: float = Field(default=1.0, ge=0.0)
    faithfulness_weight: float = Field(default=1.0, ge=0.0)
    relevance_weight: float = Field(default=1.0, ge=0.0)


class RagEvalOverallResponse(BaseModel):
    overall_score: Optional[float] = None
    recall_avg: Optional[float] = None
    faithfulness_avg: Optional[float] = None
    relevance_avg: Optional[float] = None
    weights: Dict[str, float]
    run_ids: Dict[str, str]
