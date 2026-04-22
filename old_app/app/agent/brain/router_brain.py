import json
from typing import Any

from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

from .llm_client import oai_client, extract_reasoning_summaries

ROUTER_MODEL = "gpt-5-mini"
TOP_K_MODEL = "gpt-5-mini"
SQL_MODEL = "gpt-5-mini"

ROUTER_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "router_decision",
    "description": "Decide whether to use business RAG, SQL, or a general LLM answer.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "route": {"type": "string", "enum": ["rag", "general", "sql"]},
            "confidence": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["route", "confidence", "rationale"],
    },
    "strict": True,
}

TOP_K_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "top_k_decision",
    "description": "Choose a retrieval top_k value based on query complexity and ambiguity.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "top_k": {"type": "integer"},
            "rationale": {"type": "string"},
        },
        "required": ["top_k", "rationale"],
    },
    "strict": True,
}

SQL_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "sql_generation",
    "description": "Generate a safe single-statement SELECT SQL query.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "sql": {"type": "string"},
            "rationale": {"type": "string"},
        },
        "required": ["sql", "rationale"],
    },
    "strict": True,
}

SQL_SCHEMA_HINTS = (
    "Tables and columns (PostgreSQL):\n"
    "- payroll_history (finalized payroll records): id, ten_id, biz_id, employee_id, full_name, "
    "period_start, period_end, period_key, pay_date, gross, net, total_deduction, bonus, tax, cpp, "
    "ei, regular_hours, overtime_hours, annual_salary_snapshot, hourly_rate_snapshot, status, excluded.\n"
    "- payroll_entries (draft payroll entries): id, ten_id, biz_id, employee_id, full_name, "
    "period_start, period_end, period_key, pay_date, gross, net, total_deduction, bonus, tax, cpp, "
    "ei, regular_hours, overtime_hours, annual_salary_snapshot, hourly_rate_snapshot, status, excluded.\n"
    "- employees: id, ten_id, biz_id, first_name, last_name, full_name, employment_type, "
    "hourly_rate, annual_salary, start_date, end_date, email, phone.\n"
    "- payroll_periods: id, ten_id, biz_id, payroll_schedule_id, start_date, end_date, "
    "pay_date, period_key, period_number, status.\n"
    "- payroll_schedules: id, ten_id, biz_id, frequency, payon, effective_from, "
    "effective_to, status.\n"
    "- invoices: id, ten_id, biz_id, description, amount, status, due_date.\n"
    "- biz_entities: id, ten_id, biz_id, name, legal_name, business_number, province, country, employee_count.\n"
    "Notes: Most tables include id, ten_id, biz_id, created_at. Prefer payroll_history for finalized reporting.\n"
)


def should_force_sql(query: str) -> tuple[bool, str]:
    lowered = (query or "").lower()
    keywords = [
        "total",        "sum",        "count",        "average",        "avg",
        "min",        "max",        "median",        "how many",        "how much",
        "breakdown",        "by month",        "by employee",        "by department",
        "group by",        "per month",        "per employee",        "per department",
    ]
    for kw in keywords:
        if kw in lowered:
            return True, kw
    return False, ""


async def decide_route(query: str) -> tuple[dict[str, Any], list[str]]:
    system_msg = (
        "You are a router for a payroll and business assistant. "
        "Choose 'sql' when the question can be answered precisely with a single "
        "SELECT query over the business database (lists, counts, totals, exact fields). "
        "Choose 'rag' when the question needs semantic search or narrative answers "
        "grounded in retrieved text chunks. "
        "Choose 'general' for general knowledge, definitions, or advice not tied to "
        "company-specific records. If unsure, choose 'rag'. "
        "Return JSON that matches the schema."
    )

    text_config: ResponseTextConfigParam = {"format": ROUTER_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=ROUTER_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": query},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        payload: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = {
            "route": "rag",
            "confidence": 0.0,
            "rationale": "Router output was not valid JSON; defaulted to rag.",
        }

    if payload.get("route") not in {"rag", "general", "sql"}:
        payload["route"] = "rag"
    if not isinstance(payload.get("confidence"), (int, float)):
        payload["confidence"] = 0.0
    if not isinstance(payload.get("rationale"), str):
        payload["rationale"] = "Router rationale missing; defaulted to rag."

    return payload, extract_reasoning_summaries(response)


async def decide_top_k(
    query: str,
    default_top_k: int,
    min_k: int = 3,
    max_k: int = 100,
) -> tuple[int, str, list[str]]:
    system_msg = (
        "You choose a retrieval top_k for RAG. "
        "Use higher values for short/ambiguous queries and lower values for specific queries. "
        f"Return an integer between {min_k} and {max_k}."
    )

    text_config: ResponseTextConfigParam = {"format": TOP_K_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=TOP_K_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": query},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        payload: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = {"top_k": default_top_k, "rationale": "Invalid JSON; using default."}

    top_k = payload.get("top_k", default_top_k)
    if not isinstance(top_k, int):
        top_k = default_top_k
    top_k = max(min_k, min(max_k, top_k))

    rationale = payload.get("rationale") if isinstance(payload.get("rationale"), str) else ""
    return top_k, rationale, extract_reasoning_summaries(response)


async def generate_sql(query: str) -> tuple[str, str, list[str]]:
    system_msg = (
        "You generate a SINGLE SELECT SQL query for the user's request. "
        "Only SELECT (or WITH ... SELECT) is allowed. "
        "No semicolons, no comments, no data modification. "
        "Use only the table names listed in the schema hints. "
        "Return JSON that matches the schema."
    )

    text_config: ResponseTextConfigParam = {"format": SQL_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=SQL_MODEL,
        input=[
            {"role": "system", "content": system_msg},
            {"role": "system", "content": SQL_SCHEMA_HINTS},
            {"role": "user", "content": query},
        ],
        text=text_config,
        reasoning={"summary": "auto"},
    )

    raw_text = response.output_text or ""
    try:
        payload: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError:
        payload = {"sql": "", "rationale": "Invalid JSON from SQL generator."}

    sql = payload.get("sql") if isinstance(payload.get("sql"), str) else ""
    rationale = payload.get("rationale") if isinstance(payload.get("rationale"), str) else ""
    return sql, rationale, extract_reasoning_summaries(response)
