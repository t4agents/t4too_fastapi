from __future__ import annotations

from datetime import date, timedelta


FREQUENCY_CODE_MAP: dict[str, str] = {
    "weekly": "w",
    "biweekly": "b",
    "semimonthly": "s",
    "monthly": "m",
}


def period_key_from_dates(
    frequency: str | None,
    period_start: date,
    period_end: date,
) -> str:
    freq = (frequency or "").lower()
    code = FREQUENCY_CODE_MAP.get(freq)
    if not code:
        raise ValueError(f"Unsupported payroll frequency '{frequency}' for period key")

    year = period_start.year

    if freq == "monthly":
        period_no = period_start.month
    elif freq == "semimonthly":
        half_index = 1 if period_start.day <= 15 else 2
        period_no = ((period_start.month - 1) * 2) + half_index
    elif freq in {"weekly", "biweekly"}:
        period_no = _weekly_period_number(period_start, freq)
    else:
        raise ValueError(f"Unsupported payroll frequency '{frequency}' for period key")

    return f"{period_no}-{code}-{year}"


def _weekly_period_number(period_start: date, freq: str) -> int:
    # Payroll weeks are anchored to Mondays within the calendar year.
    period_anchor = _monday_of_week(period_start)
    first_monday = _first_monday_of_year(period_anchor.year)
    delta_days = (period_anchor - first_monday).days
    if delta_days < 0:
        delta_days = 0
    divisor = 14 if freq == "biweekly" else 7
    return (delta_days // divisor) + 1


def _monday_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _first_monday_of_year(year: int) -> date:
    jan1 = date(year, 1, 1)
    offset = (7 - jan1.weekday()) % 7
    return jan1 + timedelta(days=offset)
