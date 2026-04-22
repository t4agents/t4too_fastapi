import json
import logging
import re
import time
from datetime import datetime
from typing import Any

from sqlalchemy import select, func, case

from app.agent.brain.llm_client import oai_client
from app.config import get_settings_singleton
from app.db.db_async import T4DbSession
from app.db.models.ai_guardrail import GuardrailEventDB
from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

logger = logging.getLogger("app.http")
settings = get_settings_singleton()

JUDGE_MODEL = "gpt-5-mini"

HALLUCINATION_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "hallucination_judgement",
    "description": "Judge whether the answer is fully supported by the evidence.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_hallucination": {"type": "boolean"},
            "rationale": {"type": "string"},
        },
        "required": ["is_hallucination", "rationale"],
    },
    "strict": True,
}


def _now_utc() -> datetime:
    return datetime.utcnow()


def _parse_pricing() -> dict[str, dict[str, float]]:
    if not settings.MODEL_PRICING_JSON:
        return {}
    try:
        data = json.loads(settings.MODEL_PRICING_JSON)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    pricing: dict[str, dict[str, float]] = {}
    for model, entry in data.items():
        if not isinstance(entry, dict):
            continue
        in_rate = entry.get("input")
        out_rate = entry.get("output")
        if isinstance(in_rate, (int, float)) and isinstance(out_rate, (int, float)):
            pricing[str(model)] = {"input": float(in_rate), "output": float(out_rate)}
    return pricing


def _extract_usage(usage: dict | None) -> tuple[int | None, int | None, int | None]:
    if not usage:
        return None, None, None
    input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens")
    output_tokens = usage.get("output_tokens") or usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = int(input_tokens) + int(output_tokens)
    return (
        int(input_tokens) if input_tokens is not None else None,
        int(output_tokens) if output_tokens is not None else None,
        int(total_tokens) if total_tokens is not None else None,
    )


def _estimate_cost(model: str | None, usage: dict | None) -> float | None:
    if not model or not usage:
        return None
    pricing = _parse_pricing()
    if model not in pricing:
        return None
    in_rate = pricing[model]["input"]
    out_rate = pricing[model]["output"]
    input_tokens, output_tokens, _total_tokens = _extract_usage(usage)
    if input_tokens is None or output_tokens is None:
        return None
    return (input_tokens / 1000.0) * in_rate + (output_tokens / 1000.0) * out_rate


def _is_refusal_heuristic(answer: str | None) -> bool | None:
    if not answer:
        return None
    text = answer.strip().lower()
    if not text:
        return None
    patterns = [
        r"\bi cannot\b",
        r"\bi can't\b",
        r"\bi can not\b",
        r"\bunable to\b",
        r"\bnot able to\b",
        r"\bcan't assist\b",
        r"\bcannot assist\b",
        r"\bcan't help\b",
        r"\bcannot help\b",
        r"\bnot allowed\b",
        r"\bpolicy\b",
        r"\brefuse\b",
    ]
    return any(re.search(p, text) for p in patterns)


async def _judge_hallucination(
    question: str,
    answer: str,
    evidence: list[dict],
) -> tuple[bool | None, str]:
    if not question or not answer or not evidence:
        return None, "missing_question_answer_or_evidence"

    evidence_payload = [
        {
            "evidence_id": e.get("evidence_id"),
            "source_id": e.get("source_id"),
            "chunk": e.get("chunk"),
        }
        for e in evidence
    ]

    system_msg = (
        "You are a compliance evaluator. Determine if the answer is fully supported by the evidence. "
        "If any claim is not supported, mark is_hallucination=true. "
        "Return JSON only."
    )
    user_payload = {
        "question": question,
        "answer": answer,
        "evidence": evidence_payload,
    }

    text_config: ResponseTextConfigParam = {"format": HALLUCINATION_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=JUDGE_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": json.dumps(user_payload)},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        return None, "Judge output not valid JSON."

    is_hallucination = payload.get("is_hallucination")
    rationale = payload.get("rationale")
    if not isinstance(is_hallucination, bool):
        is_hallucination = None
    if not isinstance(rationale, str):
        rationale = ""

    return is_hallucination, rationale


async def log_guardrail_event(
    *,
    ten_id: Any = None,
    biz_id: Any = None,
    user_id: Any = None,
    route: str | None = None,
    model: str | None = None,
    is_hallucination: bool | None = None,
    is_refusal: bool | None = None,
    is_fallback: bool | None = None,
    latency_ms: float | None = None,
    usage: dict | None = None,
    cost_usd: float | None = None,
    judge_model: str | None = None,
    meta: dict | None = None,
) -> None:
    input_tokens, output_tokens, total_tokens = _extract_usage(usage)
    async with T4DbSession() as session:
        session.add(
            GuardrailEventDB(
                ten_id=ten_id,
                biz_id=biz_id,
                user_id=user_id,
                route=route,
                model=model,
                judge_model=judge_model,
                is_hallucination=is_hallucination,
                is_refusal=is_refusal,
                is_fallback=is_fallback,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                meta=meta,
            )
        )
        await session.commit()


async def log_rag_guardrail(
    *,
    ten_id: Any = None,
    biz_id: Any = None,
    user_id: Any = None,
    route: str,
    question: str,
    answer: str,
    evidence: list[dict],
    model: str | None,
    latency_ms: float | None,
    guardrail_meta: dict | None,
) -> None:
    guardrail_meta = guardrail_meta or {}
    usage = guardrail_meta.get("usage")
    fallback_reason = guardrail_meta.get("fallback_reason")
    is_fallback = True if fallback_reason else None
    is_refusal = _is_refusal_heuristic(answer)

    try:
        from app.service.ser_ai_embedding import minimize_evidence_for_llm
        evidence = minimize_evidence_for_llm(evidence, question)
    except Exception:
        pass

    is_hallucination = None
    judge_note = None
    judge_model = None
    if settings.GUARDRAIL_ENABLE_LLM_JUDGE:
        judge_model = JUDGE_MODEL
        is_hallucination, judge_note = await _judge_hallucination(
            question=question,
            answer=answer,
            evidence=evidence,
        )

    cost_usd = _estimate_cost(model, usage)
    meta = {
        "guardrail_generated_at": _now_utc().isoformat(),
        "judge_note": judge_note,
        "fallback_reason": fallback_reason,
    }

    await log_guardrail_event(
        ten_id=ten_id,
        biz_id=biz_id,
        user_id=user_id,
        route=route,
        model=model,
        is_hallucination=is_hallucination,
        is_refusal=is_refusal,
        is_fallback=is_fallback,
        latency_ms=latency_ms,
        usage=usage,
        cost_usd=cost_usd,
        judge_model=judge_model,
        meta=meta,
    )


def _apply_filters(stmt, req):
    if req.start_ts:
        stmt = stmt.where(GuardrailEventDB.created_at >= req.start_ts)
    if req.end_ts:
        stmt = stmt.where(GuardrailEventDB.created_at <= req.end_ts)
    if req.route:
        stmt = stmt.where(GuardrailEventDB.route == req.route)
    if req.model:
        stmt = stmt.where(GuardrailEventDB.model == req.model)
    if req.ten_id:
        stmt = stmt.where(GuardrailEventDB.ten_id == req.ten_id)
    if req.biz_id:
        stmt = stmt.where(GuardrailEventDB.biz_id == req.biz_id)
    if req.user_id:
        stmt = stmt.where(GuardrailEventDB.user_id == req.user_id)
    return stmt


async def compute_rate(field_name: str, req) -> tuple[int, int, float | None]:
    field = getattr(GuardrailEventDB, field_name)
    total_expr = func.count(case((field.is_not(None), 1)))
    flagged_expr = func.count(case((field.is_(True), 1)))
    stmt = select(total_expr, flagged_expr)
    stmt = _apply_filters(stmt, req)
    async with T4DbSession() as session:
        total, flagged = (await session.execute(stmt)).one()
    total = int(total or 0)
    flagged = int(flagged or 0)
    rate = None if total == 0 else flagged / total
    return total, flagged, rate


async def fetch_values(field_name: str, req) -> list[float]:
    field = getattr(GuardrailEventDB, field_name)
    stmt = select(field).where(field.is_not(None))
    stmt = _apply_filters(stmt, req).order_by(GuardrailEventDB.created_at.desc())
    if req.max_rows:
        stmt = stmt.limit(req.max_rows)
    async with T4DbSession() as session:
        rows = (await session.execute(stmt)).scalars().all()
    return [float(v) for v in rows if v is not None]


def percentile(values: list[float], percentile_value: float) -> float | None:
    if not values:
        return None
    if percentile_value <= 0:
        return min(values)
    if percentile_value >= 100:
        return max(values)
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    rank = int((percentile_value / 100) * n)
    idx = max(0, min(n - 1, rank - 1))
    return sorted_vals[idx]
