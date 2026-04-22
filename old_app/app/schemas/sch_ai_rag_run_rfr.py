from pydantic import BaseModel, Field

from app.schemas.sch_ai_rag_recall import RagEvalRecallResponse
from app.schemas.sch_ai_rag_faithfulness import RagEvalFaithfulnessResponse
from app.schemas.sch_ai_rag_answer_relevance import RagEvalAnswerRelevanceResponse


class RagEvalRunRFRRequest(BaseModel):
    top_k: int = Field(default=5, ge=1)
    limit: int = Field(default=30, ge=1)
    category: str = Field(default="rag", min_length=1)
    description: str = Field(default="RAG recall+faithfulness+relevance run", min_length=1)
    judge: bool = False
    include_rows: bool = True


class RagEvalRunRFRResponse(BaseModel):
    recall: RagEvalRecallResponse
    faithfulness: RagEvalFaithfulnessResponse
    relevance: RagEvalAnswerRelevanceResponse
