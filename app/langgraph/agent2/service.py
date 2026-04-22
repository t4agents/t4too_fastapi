from collections.abc import Awaitable, Callable

from app.core.dependency_injection import ZMeDataClass
from app.langgraph.agent2.graph import compiled_workflow
from app.langgraph.agent2.state import Agent2State
from app.schemas.sch_ai_router import RouterQueryRequest


StatusCallback = Callable[[str, dict], Awaitable[None] | None]


async def route_and_answer(
    payload: RouterQueryRequest,
    zme: ZMeDataClass,
    status_cb: StatusCallback | None = None,
) -> dict:
    initial_state: Agent2State = {
        "query": payload.query,
        "top_k": payload.top_k,
        "zme": zme,
        "status_cb": status_cb,
    }
    result = await compiled_workflow.ainvoke(initial_state)
    return result.get("response") or {}
