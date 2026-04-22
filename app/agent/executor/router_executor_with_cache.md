import hashlib
import json
import logging

import app.agent.brain as brain, app.agent.tools as tools

from app.agent.brain import (
    SQL_MODEL,
    TOP_K_MODEL,
    decide_route,
    decide_top_k,
    generate_sql,
    should_force_sql,
)
from app.agent.tools import (
    GENERAL_MODEL,
    cache_get,
    cache_set,
    execute_sql,
    general_answer,
    run_rag_rerank,
    validate_sql_select,
)
from app.core.dependency_injection import ZMeDataClass
from app.schemas.sch_ai_router import RouterQueryRequest

logger = logging.getLogger("app.http")

ROUTE_CACHE_TTL = 900
TOPK_CACHE_TTL = 3600
SQL_GEN_CACHE_TTL = 900
SQL_RESULT_CACHE_TTL = 60
GENERAL_CACHE_TTL = 3600


def _normalize_query(query: str) -> str: return " ".join((query or "").lower().split())

def _length_bucket(query: str) -> str:
    n = len(query or "")
    if n <= 20:return "short"
    if n <= 60:return "medium"
    return "long"

def _cache_key(*parts: object) -> str:return "|".join(str(p) for p in parts)


async def route_and_answer(payload: RouterQueryRequest, zme: ZMeDataClass) -> dict:
    logger.info("----1 : router received query=%r top_k=%s", 555, payload.query, payload.top_k)

    force_sql, force_kw = should_force_sql(payload.query)
    if force_sql:
        logger.info("---- : keyword '%s' detected -> forcing SQL route",force_kw,)
        decision = {"route": "sql", "confidence": 1.0, "rationale": f"Keyword '{force_kw}' implies SQL."}
        route_reasoning: list[str] = [decision["rationale"]]
    else:
        route_cache_key = _cache_key("route", zme.ztid, _normalize_query(payload.query))
        cached_route = cache_get(route_cache_key)
        if cached_route:
            decision, route_reasoning = cached_route
            logger.info("---- : route cache hit -> route=%s", decision.get("route"),
            )
        else:
            decision, route_reasoning = await decide_route(payload.query)
            cache_set(route_cache_key, (decision, route_reasoning), ttl_seconds=ROUTE_CACHE_TTL)

    
    logger.info("---- : routing decision received route=%s confidence=%.3f",decision.get("route"),float(decision.get("confidence", 0.0)),)
    route = decision.get("route", "rag")

    if route == "rag":
        
        logger.info(
            "---- : routing to RAG -> calling rag_answer_rerank_service",
            555,
        )
        
        logger.info(
            "---- : choosing top_k via LLM router model=%s",
            555,
            TOP_K_MODEL,
        )
        topk_key = _cache_key(
            "topk",
            zme.ztid,
            _length_bucket(payload.query),
        )
        cached_topk = cache_get(topk_key)
        if cached_topk:
            decided_top_k, top_k_rationale, top_k_reasoning = cached_topk
            logger.info(
                "---- : top_k cache hit -> top_k=%s",
                555,
                decided_top_k,
            )
        else:
            decided_top_k, top_k_rationale, top_k_reasoning = await decide_top_k(
                payload.query,
                default_top_k=payload.top_k,
            )
            cache_set(topk_key, (decided_top_k, top_k_rationale, top_k_reasoning), ttl_seconds=TOPK_CACHE_TTL)
        
        logger.info(
            "---- : top_k decided=%s rationale=%s",
            555,
            decided_top_k,
            top_k_rationale or "<empty>",
        )

        rag_response = await run_rag_rerank(payload.query, decided_top_k, zme)
        
        logger.info(
            "---- : RAG response received answer_len=%s evidence_count=%s",
            555,
            len((rag_response or {}).get("answer") or ""),
            len((rag_response or {}).get("evidence") or []),
        )
        if isinstance(rag_response, dict):
            rag_response["route"] = "rag"
            if top_k_reasoning:
                rag_response["model_reasoning_summary"] = (
                    list(top_k_reasoning) + list(rag_response.get("model_reasoning_summary") or [])
                )
        return rag_response

    if route == "sql":
        
        logger.info(
            "---- : routing to SQL -> generating SQL with model=%s",
            555,
            SQL_MODEL,
        )
        sql_key = _cache_key("sqlgen", zme.ztid, _normalize_query(payload.query))
        cached_sql = cache_get(sql_key)
        if cached_sql:
            sql_text, sql_rationale, sql_reasoning = cached_sql
            logger.info(
                "---- : SQL cache hit",
                555,
            )
        else:
            sql_text, sql_rationale, sql_reasoning = await generate_sql(payload.query)
            cache_set(sql_key, (sql_text, sql_rationale, sql_reasoning), ttl_seconds=SQL_GEN_CACHE_TTL)

        
        logger.info(
            "---- : SQL generated=%s",
            555,
            sql_text.replace("\n", " ")[:500] or "<empty>",
        )

        ok, reason = validate_sql_select(sql_text)
        if not ok:
            
            logger.info(
                "---- : SQL rejected by guardrail reason=%s",
                555,
                reason,
            )
            
            logger.info(
                "---- : SQL rejected -> falling back to RAG",
                555,
            )
            rag_response = await run_rag_rerank(payload.query, payload.top_k, zme)
            if isinstance(rag_response, dict):
                rag_response["route"] = "sql"
                rag_response["sql"] = sql_text
                note = f"SQL guardrail rejected query: {reason}"
                rag_response["model_reasoning_summary"] = (
                    [note] + list(rag_response.get("model_reasoning_summary") or [])
                )
            return rag_response

        
        logger.info(
            "---- : executing SQL",
            555,
        )
        try:
            sql_hash = hashlib.sha256(sql_text.encode("utf-8")).hexdigest()[:16]
            sql_result_key = _cache_key("sqlres", zme.ztid, sql_hash)
            cached_rows = cache_get(sql_result_key)
            if cached_rows is not None:
                rows = cached_rows
                logger.info(
                    "---- : SQL result cache hit rows=%s",
                    555,
                    len(rows),
                )
            else:
                rows = await execute_sql(zme, sql_text)
                cache_set(sql_result_key, rows, ttl_seconds=SQL_RESULT_CACHE_TTL)
            answer_text = json.dumps(rows, ensure_ascii=False, indent=2)
            
            logger.info(
                "---- : SQL executed rows=%s",
                555,
                len(rows),
            )
        except Exception as exc:
            
            logger.info(
                "---- : SQL execution error=%s",
                555,
                str(exc),
            )
            
            logger.info(
                "---- : SQL failed -> falling back to RAG",
                555,
            )
            rag_response = await run_rag_rerank(payload.query, payload.top_k, zme)
            if isinstance(rag_response, dict):
                rag_response["route"] = "sql"
                rag_response["sql"] = sql_text
                note = f"SQL execution failed, fell back to RAG: {str(exc)}"
                rag_response["model_reasoning_summary"] = (
                    [note] + list(rag_response.get("model_reasoning_summary") or [])
                )
            return rag_response

        combined_reasoning = list(sql_reasoning)
        if sql_rationale:
            combined_reasoning.insert(0, sql_rationale)
        return {
            "query": payload.query,
            "route": "sql",
            "sql": sql_text,
            "top_k": payload.top_k,
            "model": SQL_MODEL,
            "rerank_model": "router-sql",
            "answer": answer_text,
            "confidence": 1.0,
            "reasoning_summary": ["SQL executed successfully."],
            "citations": [],
            "limitations": "",
            "model_reasoning_summary": combined_reasoning,
            "evidence": [],
        }

    
    logger.info(
        "---- : routing to GENERAL -> calling general answer model=%s",
        555,
        GENERAL_MODEL,
    )
    gen_key = _cache_key("general", GENERAL_MODEL, _normalize_query(payload.query))
    cached_general = cache_get(gen_key)
    if cached_general:
        general_payload, general_reasoning = cached_general
        logger.info(
            "---- : general cache hit",
            555,
        )
    else:
        general_payload, general_reasoning = await general_answer(payload.query)
        cache_set(gen_key, (general_payload, general_reasoning), ttl_seconds=GENERAL_CACHE_TTL)
    
    logger.info(
        "---- : GENERAL response received answer_len=%s",
        555,
        len((general_payload or {}).get("answer") or ""),
    )
    route_note = f"Router chose general with confidence={float(decision.get('confidence', 0.0)):.3f}."
    combined_reasoning = list(general_reasoning)
    if route_note:
        combined_reasoning.insert(0, route_note)
    return {
        "query": payload.query,
        "route": "general",
        "top_k": payload.top_k,
        "model": GENERAL_MODEL,
        "rerank_model": "router-general",
        "answer": general_payload.get("answer"),
        "confidence": general_payload.get("confidence"),
        "reasoning_summary": general_payload.get("reasoning_summary"),
        "citations": [],
        "limitations": general_payload.get("limitations"),
        "model_reasoning_summary": combined_reasoning,
        "evidence": [],
    }
