import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.dependency_injection import ZMeDataClass, get_zme
from app.langgraph.agent2 import route_and_answer as route_langgraph
from app.schemas.sch_ai_embedding import RagRerankAnswerResponse
from app.schemas.sch_ai_feedback import FeedbackCreateRequest, FeedbackCreateResponse
from app.schemas.sch_ai_router import RouterQueryRequest
from app.service.ser_ai_router import route_and_answer as route_and_answer_service
from app.service.ser_ai_feedback import log_feedback_event


routerRou = APIRouter()
logger = logging.getLogger(__name__)


@routerRou.post("/python", response_model=RagRerankAnswerResponse)
async def route_answer(
    payload: RouterQueryRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    return await route_and_answer_service(payload, zme)


@routerRou.post("/langgraph", response_model=RagRerankAnswerResponse)
async def route_answer_langgraph(
    payload: RouterQueryRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    return await route_langgraph(payload, zme)


def _format_sse(event: str, data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"

def _format_sse_comment(comment: str) -> str:
    return f": {comment}\n\n"


@routerRou.post("/lgstream")
async def route_answer_langgraph_stream(
    payload: RouterQueryRequest,
    request: Request,
    zme: ZMeDataClass = Depends(get_zme),
):
    queue: asyncio.Queue[tuple[str, dict] | None] = asyncio.Queue()
    keepalive_seconds = 15.0

    async def status_cb(status: str, meta: dict | None = None) -> None:
        await queue.put(("status", {"status": status, "meta": meta or {}}))

    async def runner() -> None:
        try:
            await queue.put(("status", {"status": "start", "meta": {"query": payload.query, "top_k": payload.top_k}}))
            result = await route_langgraph(payload, zme, status_cb=status_cb)
            await queue.put(("final", {"response": result}))
        except Exception as exc:
            logger.exception("lgstream failed", exc_info=exc)
            await queue.put(("error", {"message": "internal_error"}))
        finally:
            await queue.put(None)

    async def event_stream():
        task = asyncio.create_task(runner())
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
                except asyncio.TimeoutError:
                    yield _format_sse_comment(f"keepalive {datetime.now(timezone.utc).isoformat()}")
                    continue
                if item is None:
                    break
                event, data = item
                yield _format_sse(event, data)
        except asyncio.CancelledError:
            task.cancel()
            raise

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


@routerRou.post("/feedback", response_model=FeedbackCreateResponse)
async def submit_feedback(
    payload: FeedbackCreateRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    await log_feedback_event(payload, zme)
    return FeedbackCreateResponse()

