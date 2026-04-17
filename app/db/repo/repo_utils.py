from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _to_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return value


def coerce_model_value(model: Any, key: str, value: Any) -> Any:
    if value is None:
        return None

    table = getattr(model, "__table__", None)
    if table is None:
        return value

    column = table.columns.get(key)
    if column is None:
        return value

    if isinstance(column.type, Date):
        return _to_date(value)
    if isinstance(column.type, DateTime):
        return _to_datetime(value)

    return value


def coerce_model_values(model: Any, values: dict[str, Any]) -> dict[str, Any]:
    if not values:
        return values
    return {key: coerce_model_value(model, key, value) for key, value in values.items()}
