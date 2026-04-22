import json
from typing import Any

from openai.types.responses.response_format_text_json_schema_config_param import (
    ResponseFormatTextJSONSchemaConfigParam,
)
from openai.types.responses.response_text_config_param import ResponseTextConfigParam

from app.agent.brain.llm_client import oai_client, extract_reasoning_summaries

GENERAL_MODEL = "gpt-5-mini"

GENERAL_ANSWER_FORMAT: ResponseFormatTextJSONSchemaConfigParam = {
    "type": "json_schema",
    "name": "general_answer",
    "description": "Provide a concise answer for general queries.",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "answer": {"type": "string"},
            "confidence": {"type": "number"},
            "reasoning_summary": {"type": "array", "items": {"type": "string"}},
            "limitations": {"type": "string"},
        },
        "required": ["answer", "confidence", "reasoning_summary", "limitations"],
    },
    "strict": True,
}


async def general_answer(query: str) -> tuple[dict[str, Any], list[str]]:
    system_msg = (
        "You are a helpful assistant. Provide a concise, direct answer. "
        "If the question depends on company-specific or tenant data you do not have, "
        "say so briefly and suggest asking the business system instead. "
        "Return JSON that matches the schema."
    )

    text_config: ResponseTextConfigParam = {"format": GENERAL_ANSWER_FORMAT, "verbosity": "low"}

    response = await oai_client.responses.create(
        model=GENERAL_MODEL,
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
            "answer": raw_text.strip(),
            "confidence": 0.0,
            "reasoning_summary": ["Model output was not valid JSON."],
            "limitations": "Model output did not match the expected JSON schema.",
        }

    if not isinstance(payload.get("answer"), str):
        payload["answer"] = ""
    if not isinstance(payload.get("confidence"), (int, float)):
        payload["confidence"] = 0.0
    if not isinstance(payload.get("reasoning_summary"), list):
        payload["reasoning_summary"] = []
    if not isinstance(payload.get("limitations"), str):
        payload["limitations"] = ""

    return payload, extract_reasoning_summaries(response)
