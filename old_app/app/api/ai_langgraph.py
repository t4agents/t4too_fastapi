from fastapi import APIRouter, Depends

from app.core.dependency_injection import ZMeDataClass, get_zme
from app.schemas.sch_ai_embedding import RagRerankAnswerResponse
from app.schemas.sch_ai_router import RouterQueryRequest
from app.service.ser_ai_router import route_and_answer as route_and_answer_service

from app.langgraph.agent1.schema.sch_llm import LLMRequest, LLMState
from app.langgraph.agent1.workflow.agent_1_workflow import compiled_workflow

langRou = APIRouter()


@langRou.post("/token")
async def get_token_count(request: LLMRequest):
    initial_state: LLMState = {
        "prompt": request.prompt,
        "llm_output": "",
        "token_count": 0,
    }
    result = compiled_workflow.invoke(initial_state)
    return {
        "prompt": result["prompt"],
        "llm_output": result["llm_output"],
        "token_count": result["token_count"],
    }
