from fastapi import APIRouter

from .ai_brain import routerRou
from .ai_guardrail import guardrailRou
from .ai_langgraph import langRou
from .ai_rag import aiRagRou
from .ai_rag_eval import ragEvalRou

from .rag_basic import ragBasicRou

rouAI = APIRouter()

rouAI.include_router(ragBasicRou, prefix="/rag", tags=["ai-rag-basic"])

rouAI.include_router(aiRagRou, tags=["ai-rag"])
rouAI.include_router(guardrailRou, prefix="/guardrail", tags=["ai-guardrail"])
rouAI.include_router(ragEvalRou, prefix="/rag_eval", tags=["ai-rag-eval"])
rouAI.include_router(routerRou, prefix="/brain", tags=["ai-brain"])
rouAI.include_router(langRou, prefix="/langgraph", tags=["ai-langgraph"])
