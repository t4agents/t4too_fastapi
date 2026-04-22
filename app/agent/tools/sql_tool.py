from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text

from app.core.dependency_injection import ZMeDataClass


def coerce_json_value(value):
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


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append({k: coerce_json_value(v) for k, v in row.items()})
    return normalized


def validate_sql_select(sql: str) -> tuple[bool, str]:
    raw = (sql or "").strip()
    if not raw:
        return False, "SQL is empty."
    lowered = raw.lower()
    if ";" in lowered:
        return False, "Only single-statement SQL is allowed (no semicolons)."
    if "--" in lowered or "/*" in lowered or "*/" in lowered:
        return False, "SQL comments are not allowed."
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False, "Only SELECT queries are allowed."
    forbidden = [
        "insert ",
        "update ",
        "delete ",
        "drop ",
        "alter ",
        "create ",
        "grant ",
        "revoke ",
        "truncate ",
        "merge ",
        "copy ",
    ]
    for kw in forbidden:
        if kw in lowered:
            return False, f"Forbidden keyword detected: {kw.strip()}."
    return True, ""


async def execute_sql(zme: ZMeDataClass, sql_text: str) -> list[dict[str, Any]]:
    async with zme.zdb.begin_nested():
        result = await zme.zdb.execute(text(sql_text))
        rows = result.mappings().all()
    return normalize_rows([dict(r) for r in rows])
