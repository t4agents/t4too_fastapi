import time

from fastapi import APIRouter, Depends

from app.core.dependency_injection import ZMeDataClass, get_zme
from app.schemas.sch_ai_embedding import (
    RagAnswerResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagRerankAnswerResponse,
)
from app.service.ser_ai_embedding import rag_answer as rag_answer_service
from app.service.ser_ai_embedding import rag_answer_rerank as rag_answer_rerank_service
from app.service.ser_ai_embedding import rag_query as rag_query_service
from app.service.ser_ai_embedding import minimize_evidence_for_llm
from app.service.ser_ai_guardrail import log_rag_guardrail


embRou = APIRouter()


@embRou.post("/build-chunks")
async def build_chunks(zme: ZMeDataClass = Depends(get_zme)):
    chunks = "await WageEmbeddingRepository.build_chunks(zme)"
    return {"count": len(chunks), "sample": chunks[:3]}

@embRou.post("/rag_query", response_model=RagQueryResponse)
async def rag_query(
    payload: RagQueryRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    return await rag_query_service(payload, zme)


@embRou.post("/rag_answer", response_model=RagAnswerResponse)
async def rag_answer(
    payload: RagQueryRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    start = time.perf_counter()
    response = await rag_answer_service(payload, zme)
    latency_ms = (time.perf_counter() - start) * 1000

    guardrail_meta = response.pop("_guardrail", None)
    try:
        guardrail_evidence = minimize_evidence_for_llm(response.get("evidence") or [], payload.query)
        await log_rag_guardrail(
            ten_id=zme.ztid,
            biz_id=zme.zbid,
            user_id=zme.zuid,
            route="rag_answer",
            question=payload.query,
            answer=response.get("answer") or "",
            evidence=guardrail_evidence,
            model=response.get("model"),
            latency_ms=latency_ms,
            guardrail_meta=guardrail_meta,
        )
    except Exception:
        # Guardrail logging should never fail the request
        pass

    return response


@embRou.post("/rag_answer_rerank", response_model=RagRerankAnswerResponse)
async def rag_answer_rerank(
    payload: RagQueryRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    start = time.perf_counter()
    response = await rag_answer_rerank_service(payload, zme)
    latency_ms = (time.perf_counter() - start) * 1000

    guardrail_meta = response.pop("_guardrail", None)
    try:
        guardrail_evidence = minimize_evidence_for_llm(response.get("evidence") or [], payload.query)
        await log_rag_guardrail(
            ten_id=zme.ztid,
            biz_id=zme.zbid,
            user_id=zme.zuid,
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
