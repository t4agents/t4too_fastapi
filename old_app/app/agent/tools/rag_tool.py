import inspect
import time
from collections.abc import Awaitable, Callable

from app.core.dependency_injection import ZMeDataClass
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.agent.tools.persist_cache import persistent_cache_get, persistent_cache_set
from app.service.ser_ai_guardrail import log_rag_guardrail

RAG_RESPONSE_CACHE_TTL = 300


StatusCallback = Callable[[str, dict], Awaitable[None] | None]


async def _emit_status(status_cb: StatusCallback | None, status: str, meta: dict | None = None) -> None:
    if not status_cb:
        return
    try:
        result = status_cb(status, meta or {})
        if inspect.isawaitable(result):
            await result
    except Exception:
        return


async def run_rag_rerank(
    query: str,
    top_k: int,
    zme: ZMeDataClass,
    status_cb: StatusCallback | None = None,
) -> dict:
    start = time.perf_counter()
    await _emit_status(status_cb, "rag_cache_check", {"query": query, "top_k": top_k})
    cache_key = f"rag_answer_rerank|{zme.ztid}|{query}|{top_k}"
    cached = await persistent_cache_get(zme, cache_key)
    if cached is not None:
        await _emit_status(status_cb, "rag_cache_hit", {"query": query, "top_k": top_k})
        try:
            await log_rag_guardrail(
                ten_id=zme.ztid,
                biz_id=zme.zbid,
                user_id=zme.zuid,
                route="langgraph_rag",
                question=query,
                answer=(cached or {}).get("answer") or "",
                evidence=(cached or {}).get("evidence") or [],
                model=(cached or {}).get("model"),
                latency_ms=(time.perf_counter() - start) * 1000,
                guardrail_meta=(cached or {}).get("_guardrail"),
            )
        except Exception:
            pass
        return cached
    await _emit_status(status_cb, "rag_cache_miss", {"query": query, "top_k": top_k})

    from app.service.ser_ai_embedding import rag_answer_rerank as rag_answer_rerank_service

    rag_payload = RagQueryRequest(query=query, top_k=top_k)
    response = await rag_answer_rerank_service(rag_payload, zme, status_cb=status_cb)
    try:
        await log_rag_guardrail(
            ten_id=zme.ztid,
            biz_id=zme.zbid,
            user_id=zme.zuid,
            route="langgraph_rag",
            question=query,
            answer=(response or {}).get("answer") or "",
            evidence=(response or {}).get("evidence") or [],
            model=(response or {}).get("model"),
            latency_ms=(time.perf_counter() - start) * 1000,
            guardrail_meta=(response or {}).get("_guardrail"),
        )
    except Exception:
        pass
    await persistent_cache_set(zme, cache_key, response, ttl_seconds=RAG_RESPONSE_CACHE_TTL)
    return response
