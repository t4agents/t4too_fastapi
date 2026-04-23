from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zjwt
from app.db.conn.db_rls import get_db_rls
from app.schemas.sch_ai import JWType, RagRetrieveRes
from app.schemas.sch_ai_rag_basic import (
    RagAnswerResponse,
    QueryReq,
    RagQueryResponse,
    RagRerankAnswerResponse,
)
from app.schemas.sch_ai_feedback import FeedbackCreateRequest, FeedbackCreateResponse
from app.service.ser_ai_embedding import (minimize_evidence_for_llm,
    rag_answer,
    rag_rerank,
    rag_query,
    retrieve_hybrid_candidates,
    retrieve_keyword_candidates,
    retrieve_vector_candidates,
)
from app.service.ser_ai_feedback import log_feedback_event
from app.service.ser_ai_guardrail import log_rag_guardrail

ragUnitRou = APIRouter()
logger = logging.getLogger("app.http")


@ragUnitRou.post("/rag11_cosine", response_model=RagQueryResponse)
async def rag_query_cosine(
    payload: QueryReq,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    return await rag_query(payload, zjwt, db)


@ragUnitRou.post("/rag12_vector", response_model=RagRetrieveRes)
async def rag_query_vector(
    payload: QueryReq,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    results = await retrieve_vector_candidates(payload, zjwt, db)
    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "mode": "vector",
        "results": results,
    }


@ragUnitRou.post("/rag13_keyword", response_model=RagRetrieveRes)
async def rag_query_keyword(
    payload: QueryReq,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    results = await retrieve_keyword_candidates(payload, zjwt, db)
    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "mode": "keyword",
        "results": results,
    }


@ragUnitRou.post("/rag14_hybrid", response_model=RagRetrieveRes)
async def rag_query_hybrid(
    payload: QueryReq,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    results = await retrieve_hybrid_candidates(payload, zjwt, db)
    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "mode": "hybrid",
        "results": results,
    }





@ragUnitRou.post("/rag2_answer", response_model=RagAnswerResponse)
async def rag2_answer(
    payload: QueryReq,
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    start = time.perf_counter()
    response = await rag_answer(payload, zjwt, db)
    latency_ms = (time.perf_counter() - start) * 1000

    guardrail_meta = response.pop("_guardrail", None)
    try:
        guardrail_evidence = minimize_evidence_for_llm(response.get("evidence") or [], payload.query)
        await log_rag_guardrail(
            db,
            ten_id=zjwt.ztid,
            biz_id=zjwt.zbid,
            user_id=zjwt.zuid,
            route="rag_answer",
            question=payload.query,
            answer=response.get("answer") or "",
            evidence=guardrail_evidence,
            model=response.get("model"),
            latency_ms=latency_ms,
            guardrail_meta=guardrail_meta,
        )
    except Exception:
        pass

    return response



@ragUnitRou.post("/rag3_rerank", response_model=RagRerankAnswerResponse)
async def rag3_answer_rerank(
    payload: QueryReq,
    retrieval_mode: Literal["vector", "keyword", "hybrid"] = "hybrid",
    zjwt: JWType = Depends(get_zjwt),
    db: AsyncSession = Depends(get_db_rls),
):
    start = time.perf_counter()
    response = await rag_rerank(payload, zjwt, db=db, retrieval_mode=retrieval_mode)
    latency_ms = (time.perf_counter() - start) * 1000

    guardrail_meta = response.pop("_guardrail", None)
    try:
        guardrail_evidence = minimize_evidence_for_llm(response.get("evidence") or [], payload.query)
        await log_rag_guardrail(
            db,
            ten_id=zjwt.ztid,
            biz_id=zjwt.zbid,
            user_id=zjwt.zuid,
            route="rag_answer_rerank",
            question=payload.query,
            answer=response.get("answer") or "",
            evidence=guardrail_evidence,
            model=response.get("model"),
            latency_ms=latency_ms,
            guardrail_meta=guardrail_meta,
        )
    except Exception:
        pass

    return response


# @aiRagRou.post("/rag_answer_rerank_stream")
# async def rag_answer_rerank_stream(
#     payload: RagQueryRequest,
#     request: Request,
#     zjwt: JWType = Depends(get_zjwt),
#     db: AsyncSession = Depends(get_db_rls),
# ):
#     ctx = ai_context_from_zjwt(zjwt, db)
#     queue: asyncio.Queue[tuple[str, dict] | None] = asyncio.Queue()
#     keepalive_seconds = 15.0
#     start = time.perf_counter()

#     async def status_cb(status: str, meta: dict | None = None) -> None:
#         await queue.put(("status", {"status": status, "meta": meta or {}}))

#     async def runner() -> None:
#         try:
#             result = await rag_answer_rerank_service(payload, ctx, status_cb=status_cb)
#             latency_ms = (time.perf_counter() - start) * 1000
#             guardrail_meta = result.pop("_guardrail", None)
#             try:
#                 guardrail_evidence = minimize_evidence_for_llm(result.get("evidence") or [], payload.query)
#                 await log_rag_guardrail(
#                     db,
#                     ten_id=ctx.ten_id,
#                     biz_id=ctx.biz_id,
#                     user_id=ctx.user_id,
#                     route="rag_answer_rerank_stream",
#                     question=payload.query,
#                     answer=result.get("answer") or "",
#                     evidence=guardrail_evidence,
#                     model=result.get("model"),
#                     latency_ms=latency_ms,
#                     guardrail_meta=guardrail_meta,
#                 )
#             except Exception:
#                 pass
#             await queue.put(("final", {"response": result}))
#         except Exception as exc:
#             logger.exception("rag_answer_rerank_stream failed", exc_info=exc)
#             await queue.put(("error", {"message": "internal_error"}))
#         finally:
#             await queue.put(None)

#     async def event_stream():
#         # Emit a first chunk immediately to avoid proxy/client buffering.
#         yield _format_sse("status", {"status": "start", "meta": {"query": payload.query, "top_k": payload.top_k}})
#         task = asyncio.create_task(runner())
#         try:
#             while True:
#                 try:
#                     item = await asyncio.wait_for(queue.get(), timeout=keepalive_seconds)
#                 except asyncio.TimeoutError:
#                     yield _format_sse_comment(f"keepalive {datetime.now(timezone.utc).isoformat()}")
#                     if await request.is_disconnected():
#                         task.cancel()
#                         break
#                     continue
#                 if item is None:
#                     break
#                 event, data = item
#                 yield _format_sse(event, data)
#                 if await request.is_disconnected():
#                     task.cancel()
#                     break
#         except asyncio.CancelledError:
#             task.cancel()
#             raise

#     headers = {
#         "Cache-Control": "no-cache, no-transform",
#         "Connection": "keep-alive",
#         "X-Accel-Buffering": "no",
#     }
#     return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


# @aiRagRou.post("/feedback", response_model=FeedbackCreateResponse)
# async def submit_feedback(
#     payload: FeedbackCreateRequest,
#     zjwt: JWType = Depends(get_zjwt),
#     db: AsyncSession = Depends(get_db_rls),
# ):
#     ctx = ai_context_from_zjwt(zjwt, db)
#     await log_feedback_event(payload, ctx)
#     return FeedbackCreateResponse()
