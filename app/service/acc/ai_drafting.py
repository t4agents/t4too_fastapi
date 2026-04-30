import json
from decimal import Decimal
from typing import Any

from openai import OpenAI

from app.config import get_settings_singleton

settings = get_settings_singleton()
OPENAI_ENABLED = getattr(settings, "OPENAI_ENABLED", True)
DEFAULT_CURRENCY = getattr(settings, "DEFAULT_CURRENCY", "CAD")
DEFAULT_TAX_JURISDICTION = getattr(settings, "DEFAULT_TAX_JURISDICTION", "CA")
OPENAI_TIMEOUT_SEC = getattr(settings, "OPENAI_TIMEOUT_SEC", 30)
OPENAI_MODEL_DEFAULT = getattr(settings, "OPENAI_MODEL_DEFAULT", "gpt-5-mini")


def _fallback_draft(amount: Decimal, description: str) -> dict[str, Any]:
    abs_amount = abs(amount)
    debit_account_code = "5000" if amount < 0 else "1000"
    credit_account_code = "1000" if amount < 0 else "4000"
    return {
        "confidence": 0.62,
        "memo": description[:120],
        "rationale": "Fallback heuristic used because model output was unavailable or invalid.",
        "lines": [
            {"account_code": debit_account_code, "line_type": "debit", "amount": float(abs_amount), "note": "Auto draft"},
            {"account_code": credit_account_code, "line_type": "credit", "amount": float(abs_amount), "note": "Auto draft"},
        ],
    }


def generate_je_draft(*, amount: Decimal, description: str, accounts: list[dict[str, str]]) -> dict[str, Any]:
    api_key = __import__("os").environ.get("OPENAI_API_KEY")
    if not OPENAI_ENABLED or not api_key:
        return _fallback_draft(amount, description)

    prompt = {
        "task": "Create balanced accounting journal entry lines.",
        "currency": DEFAULT_CURRENCY,
        "jurisdiction": DEFAULT_TAX_JURISDICTION,
        "transaction": {"description": description, "amount": float(amount)},
        "chart_of_accounts": accounts,
        "output_schema": {
            "confidence": "0..1 float",
            "memo": "short memo",
            "rationale": "short explanation",
            "lines": [{"account_code": "string", "line_type": "debit|credit", "amount": "positive float", "note": "string"}],
        },
        "rules": ["Must be balanced", "Use only provided account_code values", "Return JSON only"],
    }

    try:
        client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT_SEC)
        resp = client.responses.create(
            model=OPENAI_MODEL_DEFAULT,
            input=[{"role": "user", "content": [{"type": "input_text", "text": json.dumps(prompt)}]}],
        )
        raw = (resp.output_text or "").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "lines" not in parsed:
            return _fallback_draft(amount, description)
        return parsed
    except Exception:
        return _fallback_draft(amount, description)
