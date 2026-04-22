import inspect
import json

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
from app.langgraph.agent2.state import Agent2State


async def _emit_status(
    state: Agent2State,
    status: str,
    meta: dict | None = None,
) -> None:
    cb = state.get("status_cb")
    if not cb:
        return
    try:
        result = cb(status, meta or {})
        if inspect.isawaitable(result):
            await result
    except Exception:
        # Status updates should never break the main flow.
        return


def init_state(state: Agent2State) -> Agent2State:
    return state


async def decide_route_node(state: Agent2State) -> Agent2State:
    await _emit_status(state, "routing_start", {"query": state.get("query")})
    query = state.get("query") or ""
    force_sql, force_kw = should_force_sql(query)
    if force_sql:
        decision = {
            "route": "sql",
            "confidence": 1.0,
            "rationale": f"Keyword '{force_kw}' implies SQL.",
        }
        route_reasoning = [decision["rationale"]]
    else:
        decision, route_reasoning = await decide_route(query)
    await _emit_status(
        state,
        "routing_done",
        {
            "route": decision.get("route", "rag"),
            "confidence": decision.get("confidence"),
            "rationale": decision.get("rationale"),
        },
    )
    return {
        **state,
        "decision": decision,
        "route_reasoning": list(route_reasoning or []),
        "route": decision.get("route", "rag"),
    }


async def rag_node(state: Agent2State) -> Agent2State:
    query = state.get("query") or ""
    top_k = state.get("top_k")
    await _emit_status(state, "rag_start", {"query": query, "top_k": top_k})

    decided_top_k, top_k_rationale, top_k_reasoning = await decide_top_k(
        query,
        default_top_k=top_k,
    )
    await _emit_status(
        state,
        "rag_top_k",
        {"top_k": decided_top_k, "rationale": top_k_rationale},
    )
    rag_response = await run_rag_rerank(
        query,
        decided_top_k,
        state.get("zme"),
        status_cb=state.get("status_cb"),
    )
    if isinstance(rag_response, dict):
        rag_response["route"] = "rag"
        if top_k_reasoning:
            rag_response["model_reasoning_summary"] = (
                list(top_k_reasoning) + list(rag_response.get("model_reasoning_summary") or [])
            )
        rag_response["top_k"] = decided_top_k
        rag_response["model"] = TOP_K_MODEL
    await _emit_status(
        state,
        "rag_done",
        {"top_k": decided_top_k, "model": TOP_K_MODEL},
    )

    return {
        **state,
        "rag_response": rag_response,
        "response": rag_response,
    }


async def sql_node(state: Agent2State) -> Agent2State:
    query = state.get("query") or ""
    zme = state.get("zme")
    top_k = state.get("top_k")
    await _emit_status(state, "sql_start", {"query": query})

    sql_text, sql_rationale, sql_reasoning = await generate_sql(query)
    await _emit_status(state, "sql_generated", {"sql": sql_text})

    ok, reason = validate_sql_select(sql_text)
    if not ok:
        await _emit_status(state, "sql_guardrail_rejected", {"reason": reason, "sql": sql_text})
        rag_response = await run_rag_rerank(
            query,
            top_k,
            zme,
            status_cb=state.get("status_cb"),
        )
        if isinstance(rag_response, dict):
            rag_response["route"] = "sql"
            rag_response["sql"] = sql_text
            note = f"SQL guardrail rejected query: {reason}"
            rag_response["model_reasoning_summary"] = (
                [note] + list(rag_response.get("model_reasoning_summary") or [])
            )
        return {
            **state,
            "sql_text": sql_text,
            "response": rag_response,
        }

    try:
        await _emit_status(state, "sql_execute", {"sql": sql_text})
        rows = await execute_sql(zme, sql_text)
        answer_text = json.dumps(rows, ensure_ascii=False, indent=2)
    except Exception as exc:
        await _emit_status(state, "sql_execute_failed", {"error": str(exc), "sql": sql_text})
        rag_response = await run_rag_rerank(
            query,
            top_k,
            zme,
            status_cb=state.get("status_cb"),
        )
        if isinstance(rag_response, dict):
            rag_response["route"] = "sql"
            rag_response["sql"] = sql_text
            note = f"SQL execution failed, fell back to RAG: {str(exc)}"
            rag_response["model_reasoning_summary"] = (
                [note] + list(rag_response.get("model_reasoning_summary") or [])
            )
        return {
            **state,
            "sql_text": sql_text,
            "response": rag_response,
        }

    combined_reasoning = list(sql_reasoning or [])
    if sql_rationale:
        combined_reasoning.insert(0, sql_rationale)
    response = {
        "query": query,
        "route": "sql",
        "sql": sql_text,
        "top_k": top_k,
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
    await _emit_status(
        state,
        "sql_done",
        {"row_count": len(rows), "model": SQL_MODEL},
    )

    return {
        **state,
        "sql_text": sql_text,
        "sql_rationale": sql_rationale,
        "sql_reasoning": list(sql_reasoning or []),
        "response": response,
    }


async def general_node(state: Agent2State) -> Agent2State:
    query = state.get("query") or ""
    decision = state.get("decision") or {}
    await _emit_status(state, "general_start", {"query": query})

    general_payload, general_reasoning = await general_answer(query)
    route_note = f"Router chose general with confidence={float(decision.get('confidence', 0.0)):.3f}."
    combined_reasoning = list(general_reasoning or [])
    if route_note:
        combined_reasoning.insert(0, route_note)

    response = {
        "query": query,
        "route": "general",
        "top_k": state.get("top_k"),
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
    await _emit_status(state, "general_done", {"model": GENERAL_MODEL})

    return {
        **state,
        "general_payload": general_payload,
        "general_reasoning": list(general_reasoning or []),
        "response": response,
    }
