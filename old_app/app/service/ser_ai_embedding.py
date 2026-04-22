import inspect
import json
import logging
import hashlib
import re
from collections.abc import Awaitable, Callable
from typing import Any
import aiohttp
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from openai import AsyncOpenAI
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from fastapi import HTTPException
from sqlalchemy import func, select, cast, literal
from sqlalchemy.dialects.postgresql import REGCONFIG
from sqlalchemy.inspection import inspect

from app.config import get_settings_singleton
from app.core.dependency_injection import ZMeDataClass
from app.db.models.ai_embedding import Embedding384
from app.db.models.m_payroll_history import PayrollHistory
from app.llm.conn.openai_embedder import embed_fn
from app.schemas.sch_ai_embedding import RagQueryRequest
from app.agent.tools.persist_cache import persistent_cache_get, persistent_cache_set


settings = get_settings_singleton()
oai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger("app.http")
ANSWER_MODEL = "gpt-5-mini"
COHERE_RERANK_MODEL = "rerank-v3.5"
COHERE_RERANK_URL = "https://api.cohere.com/v1/rerank"
COHERE_RERANK_CACHE_TTL = 900
EMBED_CACHE_TTL = 3600
RETRIEVAL_CACHE_TTL = 300

RAG_ANSWER_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "rag_answer",
    "description": "Generate a concise, auditable answer grounded only in provided evidence.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "reasoning_summary": {"type": "array", "items": {"type": "string"}},
            "citations": {"type": "array", "items": {"type": "integer"}},
            "limitations": {"type": "string"},
        },
        "required": ["answer", "confidence", "reasoning_summary", "citations", "limitations"],
    },
    "strict": True,
}

_PII_CORE_FIELDS: tuple[str, ...] = (
    "employment_type",
    "period_key",
    "pay_date",
    "gross",
    "net",
    "total_deduction",
    "regular_hours",
    "overtime_hours",
    "cpp",
    "ei",
    "tax",
    "status",
    "excluded",
)

_PII_OPTIONAL_FIELDS: dict[str, tuple[str, ...]] = {
    "bonus": ("bonus",),
    "vacation": ("vacation",),
    "annual_salary_snapshot": ("salary", "annual salary"),
    "hourly_rate_snapshot": ("hourly", "hourly rate"),
    "period_start": ("period start", "start date", "period begin"),
    "period_end": ("period end", "end date", "period finish"),
    "adjustment": ("adjustment",),
}


def _fmt_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _should_include_name(question: str | None) -> bool:
    if not question:
        return False
    text = question.lower()
    return any(
        token in text
        for token in (
            "full name",
            "name",
            "who",
            "employee name",
            "person",
            "identity",
        )
    )


def _fields_needed_for_question(question: str | None) -> list[str]:
    fields: list[str] = list(_PII_CORE_FIELDS)
    if not question:
        return fields
    text = question.lower()
    for field, keywords in _PII_OPTIONAL_FIELDS.items():
        if any(keyword in text for keyword in keywords) and field not in fields:
            fields.append(field)
    return fields


def _build_minimized_chunk(history: dict[str, Any], fields: list[str]) -> str:
    parts: list[str] = []
    for key in fields:
        if key not in history:
            continue
        value = _fmt_value(history.get(key))
        if value == "":
            continue
        parts.append(f"{key}={value}")
    return " | ".join(parts)


def _redact_chunk_basic(text: str, include_name: bool) -> str:
    if not text:
        return ""
    redacted = text
    if not include_name:
        redacted = re.sub(r"(full_name\\s*[:=]\\s*)([^|\\n]+)", r"\\1[REDACTED]", redacted, flags=re.IGNORECASE)
        redacted = re.sub(r"(full name\\s*[:=]\\s*)([^|\\n]+)", r"\\1[REDACTED]", redacted, flags=re.IGNORECASE)
        redacted = re.sub(r"(name\\s*[:=]\\s*)([^|\\n]+)", r"\\1[REDACTED]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", "[REDACTED_EMAIL]", redacted, flags=re.IGNORECASE)
    redacted = re.sub(r"\\b\\+?\\d[\\d\\s().-]{7,}\\b", "[REDACTED_PHONE]", redacted)
    return redacted


def minimize_evidence_for_llm(evidence: list[dict], question: str | None) -> list[dict]:
    if not settings.PII_MINIMIZE_RAG_EVIDENCE:
        return evidence
    include_name = _should_include_name(question)
    fields = _fields_needed_for_question(question)
    if include_name:
        if "full_name" not in fields:
            fields = ["full_name"] + fields

    minimized: list[dict] = []
    for item in evidence:
        history = item.get("history")
        if isinstance(history, dict):
            minimal_history = {k: history.get(k) for k in fields if k in history}
            chunk = _build_minimized_chunk(minimal_history, fields)
            if not chunk:
                chunk = _redact_chunk_basic(str(item.get("chunk") or ""), include_name)
        else:
            minimal_history = None
            chunk = _redact_chunk_basic(str(item.get("chunk") or ""), include_name)

        cleaned = dict(item)
        cleaned["chunk"] = chunk
        if minimal_history is not None:
            cleaned["history"] = minimal_history
        else:
            cleaned.pop("history", None)
        minimized.append(cleaned)
    return minimized


def _coerce_json_value(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "tolist"):
        return value.tolist()
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, dict)):
        try:
            return list(value)
        except TypeError:
            pass
    return value


def _orm_to_dict(obj) -> dict[str, Any]:
    return {c.key: _coerce_json_value(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs}


def _extract_reasoning_summaries(response) -> list[str]:
    summaries: list[str] = []
    for item in getattr(response, "output", []) or []:
        if getattr(item, "type", None) != "reasoning":
            continue
        for s in getattr(item, "summary", []) or []:
            if getattr(s, "type", None) == "summary_text":
                summaries.append(s.text)
    return summaries


def _extract_usage(response) -> dict | None:
    usage = getattr(response, "usage", None)
    if not usage:
        return None
    payload = {}
    for key in ("input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens"):
        value = getattr(usage, key, None)
        if value is not None:
            payload[key] = value
    return payload or None


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


async def _generate_answer(question: str, evidence: list[dict]) -> tuple[dict, list[str], dict | None]:
    system_msg = (
        "You are an auditing assistant. Answer the question using ONLY the evidence provided. "
        "Be concise, factual, and suitable for audit. Do NOT invent facts. "
        "Return JSON that matches the schema. "
        "For citations, list the evidence_id values you relied on."
    )
    user_payload = {
        "question": question,
        "evidence": evidence,
    }

    text_config: ResponseTextConfigParam = {"format": RAG_ANSWER_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=ANSWER_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        answer_payload = json.loads(raw_text)
    except json.JSONDecodeError:
        answer_payload = {
            "answer": raw_text.strip(),
            "confidence": 0.0,
            "reasoning_summary": ["Model output was not valid JSON."],
            "citations": [],
            "limitations": "Model output did not match the expected JSON schema.",
        }

    return answer_payload, _extract_reasoning_summaries(response), _extract_usage(response)


async def _cohere_rerank(query: str, documents: list[str], top_n: int) -> list[dict]:
    if not settings.COHERE_API_KEY:
        raise HTTPException(status_code=500, detail="COHERE_API_KEY is not configured.")

    payload = {
        "model": COHERE_RERANK_MODEL,
        "query": query,
        "documents": documents,
        "top_n": top_n,
    }
    headers = {
        "Authorization": f"Bearer {settings.COHERE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(COHERE_RERANK_URL, json=payload, headers=headers) as resp:
            data = await resp.json()
            if resp.status >= 400:
                raise HTTPException(status_code=resp.status, detail=data)
            return data.get("results", [])


async def _retrieve_hybrid_candidates(payload: RagQueryRequest, zme: ZMeDataClass) -> list[dict]:
    retrieval_cache_key = f"rag_candidates|{zme.ztid}|{payload.query}|{payload.top_k}"
    cached_candidates = await persistent_cache_get(zme, retrieval_cache_key)
    if cached_candidates is not None:
        logger.info("---------------- Retrieval cache hit -> candidates=%s", len(cached_candidates))
        return cached_candidates

    regconfig = cast(literal("english"), REGCONFIG)
    tsv = func.to_tsvector(regconfig, Embedding384.chunk)
    tsq = func.plainto_tsquery(regconfig, payload.query)
    kw_score = func.ts_rank_cd(tsv, tsq).label("kw_score")
    kw_score = func.least(kw_score * 10, 1.0).label("kw_score")

    embed_cache_key = f"embed_query|{zme.ztid}|{payload.query}"
    cached_embedding = await persistent_cache_get(zme, embed_cache_key)
    if cached_embedding is not None:
        query_vec = cached_embedding
        logger.info("---------------- Embedding cache hit")
    else:
        query_vec = await embed_fn(payload.query)
        await persistent_cache_set(zme, embed_cache_key, query_vec, ttl_seconds=EMBED_CACHE_TTL)
    distance = Embedding384.emb384.cosine_distance(query_vec).label("distance")
    vec_score = func.coalesce(1 - distance, 0).label("vec_score")

    stmt = (
        select(
            Embedding384,
            PayrollHistory,
            vec_score,
            kw_score,
            (vec_score * 0.7 + kw_score * 0.3).label("final_score"),
        )
        .join(PayrollHistory, PayrollHistory.id == Embedding384.source_id)
        .where(PayrollHistory.biz_id == zme.zbid)
        .order_by(func.coalesce((vec_score * 0.7 + kw_score * 0.3), vec_score).desc())
        .limit(payload.top_k)
    )
    res = await zme.zdb.execute(stmt)
    rows = res.all()

    candidates = []
    for idx, (emb_row, hist_row, vec_score, kw_score, final_score) in enumerate(rows, start=1):
        score = float(final_score) if final_score is not None else float(vec_score)
        candidates.append(
            {
                "evidence_id": idx,
                "score": score,
                "source_id": str(emb_row.source_id),
                "chunk": emb_row.chunk,
                "history": _orm_to_dict(hist_row),
            }
        )
    await persistent_cache_set(zme, retrieval_cache_key, candidates, ttl_seconds=RETRIEVAL_CACHE_TTL)
    return candidates


async def rag_query(payload: RagQueryRequest, zme: ZMeDataClass) -> dict:
    embed_cache_key = f"embed_query|{zme.ztid}|{payload.query}"
    cached_embedding = await persistent_cache_get(zme, embed_cache_key)
    if cached_embedding is not None:
        query_vec = cached_embedding
        logger.info("---------------- Embedding cache hit")
    else:
        query_vec = await embed_fn(payload.query)
        await persistent_cache_set(zme, embed_cache_key, query_vec, ttl_seconds=EMBED_CACHE_TTL)
    distance = Embedding384.emb384.cosine_distance(query_vec).label("distance")

    stmt = (
        select(Embedding384, PayrollHistory, distance)
        .join(PayrollHistory, PayrollHistory.id == Embedding384.source_id)
        .where(PayrollHistory.biz_id == zme.zbid)
        .order_by(distance.asc())
        .limit(payload.top_k)
    )
    res = await zme.zdb.execute(stmt)
    rows = res.all()

    results = []
    for emb_row, hist_row, dist in rows:
        score = None if dist is None else 1 - float(dist)
        results.append(
            {
                "score": score,
                "distance": None if dist is None else float(dist),
                "embedding": _orm_to_dict(emb_row),
                "history": _orm_to_dict(hist_row),
            }
        )

    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "results": results,
    }


async def rag_answer(payload: RagQueryRequest, zme: ZMeDataClass) -> dict:
    evidence = await _retrieve_hybrid_candidates(payload, zme)

    if not evidence:
        return {
            "query": payload.query,
            "top_k": payload.top_k,
            "model": ANSWER_MODEL,
            "answer": "No matching payroll history found for this query.",
            "confidence": 0,
            "reasoning_summary": ["No evidence was retrieved for the query."],
            "citations": [],
            "limitations": "No relevant payroll history records were retrieved.",
            "model_reasoning_summary": [],
            "evidence": [],
        }

    llm_evidence = minimize_evidence_for_llm(evidence, payload.query)
    answer_payload, reasoning_summary, usage = await _generate_answer(payload.query, llm_evidence)

    return {
        "query": payload.query,
        "top_k": payload.top_k,
        "model": ANSWER_MODEL,
        "answer": answer_payload.get("answer"),
        "confidence": answer_payload.get("confidence"),
        "reasoning_summary": answer_payload.get("reasoning_summary"),
        "citations": answer_payload.get("citations"),
        "limitations": answer_payload.get("limitations"),
        "model_reasoning_summary": reasoning_summary,
        "evidence": evidence,
        "_guardrail": {
            "usage": usage,
        },
    }


async def rag_answer_rerank(
    payload: RagQueryRequest,
    zme: ZMeDataClass,
    status_cb: StatusCallback | None = None,
) -> dict:
    await _emit_status(
        status_cb,
        "rag_retrieve_start",
        {"query": payload.query, "top_k": payload.top_k},
    )
    evidence = await _retrieve_hybrid_candidates(payload, zme)
    await _emit_status(
        status_cb,
        "rag_retrieve_done",
        {"count": len(evidence), "top_k": payload.top_k},
    )
    if not evidence:
        await _emit_status(status_cb, "rag_no_evidence", {"query": payload.query})
        return {
            "query": payload.query,
            "top_k": payload.top_k,
            "model": ANSWER_MODEL,
            "rerank_model": COHERE_RERANK_MODEL,
            "answer": "No matching payroll history found for this query.",
            "confidence": 0,
            "reasoning_summary": ["No evidence was retrieved for the query."],
            "citations": [],
            "limitations": "No relevant payroll history records were retrieved.",
            "model_reasoning_summary": [],
            "evidence": [],
        }

    llm_evidence = minimize_evidence_for_llm(evidence, payload.query)
    documents = [item["chunk"] for item in llm_evidence]
    fallback_reason: str | None = None
    try:
        await _emit_status(
            status_cb,
            "rag_rerank_start",
            {"model": COHERE_RERANK_MODEL, "top_k": payload.top_k},
        )
        joined = "\n".join(documents)
        docs_hash = hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]
        cache_key = f"cohere_rerank|{zme.ztid}|{payload.query}|{payload.top_k}|{docs_hash}"
        cached_rerank = await persistent_cache_get(zme, cache_key)
        if cached_rerank is not None:
            rerank_results = cached_rerank
            logger.info(
                "---------------- Cohere rerank cache hit -> results=%s",
                len(rerank_results),
            )
        else:
            rerank_results = await _cohere_rerank(payload.query, documents, payload.top_k)
            await persistent_cache_set(zme, cache_key, rerank_results, ttl_seconds=COHERE_RERANK_CACHE_TTL)
        await _emit_status(
            status_cb,
            "rag_rerank_done",
            {"count": len(rerank_results), "model": COHERE_RERANK_MODEL},
        )
    except HTTPException as exc:
        if exc.status_code == 429 or (exc.status_code is not None and exc.status_code >= 500):
            fallback_reason = f"Cohere rerank unavailable (status {exc.status_code})."
        else:
            raise
    except Exception as exc:
        fallback_reason = f"Cohere rerank failed: {str(exc)}"

    if fallback_reason:
        await _emit_status(
            status_cb,
            "rag_rerank_fallback",
            {"reason": fallback_reason, "model": COHERE_RERANK_MODEL},
        )
        logger.info("---------------- Cohere rerank fallback -> using base evidence. reason=%s", fallback_reason)
        reranked = [
            {
                "evidence_id": idx,
                "score": item.get("score"),
                "source_id": item.get("source_id"),
                "chunk": item["chunk"],
                "history": item["history"],
            }
            for idx, item in enumerate(evidence, start=1)
        ]
    else:
        reranked = []
        for new_idx, item in enumerate(rerank_results, start=1):
            idx = item.get("index")
            if idx is None or idx >= len(evidence):
                continue
            base = evidence[idx]
            reranked.append(
                {
                    "evidence_id": new_idx,
                    "score": item.get("relevance_score"),
                    "source_id": base.get("source_id"),
                    "chunk": base["chunk"],
                    "history": base["history"],
                }
            )

    await _emit_status(status_cb, "rag_generate_start", {"model": ANSWER_MODEL})
    llm_reranked = minimize_evidence_for_llm(reranked, payload.query)
    answer_payload, reasoning_summary, usage = await _generate_answer(payload.query, llm_reranked)
    await _emit_status(status_cb, "rag_generate_done", {"model": ANSWER_MODEL})
    if fallback_reason:
        reasoning_summary = [fallback_reason] + list(reasoning_summary)
        limitations = answer_payload.get("limitations") or ""
        if limitations:
            limitations = f"{limitations} Rerank fallback: {fallback_reason}"
        else:
            limitations = f"Rerank fallback: {fallback_reason}"
        answer_payload["limitations"] = limitations

    response = {
        "query": payload.query,
        "top_k": payload.top_k,
        "model": ANSWER_MODEL,
        "rerank_model": COHERE_RERANK_MODEL,
        "answer": answer_payload.get("answer"),
        "confidence": answer_payload.get("confidence"),
        "reasoning_summary": answer_payload.get("reasoning_summary"),
        "citations": answer_payload.get("citations"),
        "limitations": answer_payload.get("limitations"),
        "model_reasoning_summary": reasoning_summary,
        "evidence": reranked,
    }
    response["_guardrail"] = {
        "usage": usage,
    }
    if fallback_reason:
        response["_guardrail"]["fallback_reason"] = fallback_reason
    return response
