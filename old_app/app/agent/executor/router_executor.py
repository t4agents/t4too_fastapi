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
    execute_sql,
    general_answer,
    run_rag_rerank,
    validate_sql_select,
)
from app.core.dependency_injection import ZMeDataClass
from app.schemas.sch_ai_router import RouterQueryRequest

logger = logging.getLogger("app.http")


async def route_and_answer(payload: RouterQueryRequest, zme: ZMeDataClass) -> dict:
    logger.info("----1 : router received query=%r top_k=%s", 555, payload.query, payload.top_k)

    force_sql, force_kw = should_force_sql(payload.query)
    if force_sql:
        logger.info("---- : keyword '%s' detected -> forcing SQL route",force_kw,)
        decision = {"route": "sql", "confidence": 1.0, "rationale": f"Keyword '{force_kw}' implies SQL."}
        route_reasoning: list[str] = [decision["rationale"]]
    else:
        decision, route_reasoning = await decide_route(payload.query)

    
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
        decided_top_k, top_k_rationale, top_k_reasoning = await decide_top_k(
            payload.query,
            default_top_k=payload.top_k,
        )
        
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
        sql_text, sql_rationale, sql_reasoning = await generate_sql(payload.query)

        
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
            rows = await execute_sql(zme, sql_text)
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
    general_payload, general_reasoning = await general_answer(payload.query)
    
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
