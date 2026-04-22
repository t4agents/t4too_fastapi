from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")
TWOPLACES = Decimal("0.01")

FREQUENCY_CODE_MAP: dict[str, str] = {
    "weekly": "w",
    "biweekly": "b",
    "semimonthly": "s",
    "monthly": "m",
}

# 2026 payroll constants used by legacy logic.
CPP_YMPE = Decimal("74600.00")
CPP_YAMPE = Decimal("85000.00")
CPP_BASIC_EXEMPTION = Decimal("3500.00")
CPP_BASE_RATE = Decimal("0.0495")
CPP_FIRST_ADDITIONAL_RATE = Decimal("0.0100")
CPP_TOTAL_RATE = CPP_BASE_RATE + CPP_FIRST_ADDITIONAL_RATE
CPP_MAX_BASE_PLUS = Decimal("4230.45")
CPP2_RATE = Decimal("0.0400")
CPP2_MAX = Decimal("416.00")

EI_MIE = Decimal("68900.00")
EI_RATE = Decimal("0.0163")
EI_MAX = Decimal("1123.07")

FEDERAL_LOWEST_RATE = Decimal("0.14")
FEDERAL_BPA_MAX = Decimal("16452.00")
FEDERAL_CEA_MAX = Decimal("1501.00")
FEDERAL_BRACKETS = [
    (Decimal("58523.00"), Decimal("0.1400"), Decimal("0")),
    (Decimal("117045.00"), Decimal("0.2050"), Decimal("3804")),
    (Decimal("181440.00"), Decimal("0.2600"), Decimal("10241")),
    (Decimal("258482.00"), Decimal("0.2900"), Decimal("15685")),
    (Decimal("Infinity"), Decimal("0.3300"), Decimal("26024")),
]

ONTARIO_LOWEST_RATE = Decimal("0.0505")
ONTARIO_BPA = Decimal("12989.00")
ONTARIO_BRACKETS = [
    (Decimal("53891.00"), Decimal("0.0505"), Decimal("0")),
    (Decimal("107785.00"), Decimal("0.0915"), Decimal("2210")),
    (Decimal("150000.00"), Decimal("0.1116"), Decimal("4376")),
    (Decimal("220000.00"), Decimal("0.1216"), Decimal("5876")),
    (Decimal("Infinity"), Decimal("0.1316"), Decimal("8076")),
]

ONTARIO_SURTAX_THRESHOLD_1 = Decimal("5818.00")
ONTARIO_SURTAX_THRESHOLD_2 = Decimal("7446.00")
ONTARIO_SURTAX_RATE_1 = Decimal("0.20")
ONTARIO_SURTAX_RATE_2 = Decimal("0.36")
ONTARIO_TAX_REDUCTION_BASIC = Decimal("300.00")


def period_key_from_dates(frequency: str | None, period_start: date, period_end: date) -> str:
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


def periods_per_year_from_frequency(frequency: str | None) -> int:
    mapping = {
        "weekly": 52,
        "biweekly": 26,
        "semimonthly": 24,
        "monthly": 12,
        "quarterly": 4,
        "annually": 1,
    }
    return int(mapping.get((frequency or "").lower(), 1))


def calculate_payroll_deductions_on_2026(
    period_gross: Decimal,
    periods_per_year: int,
    cpp_exempt: bool = False,
    ei_exempt: bool = False,
    federal_basic_personal_amount: Decimal | None = None,
    ontario_basic_personal_amount: Decimal | None = None,
) -> dict[str, Decimal]:
    if period_gross is None:
        period_gross = ZERO

    periods = Decimal(periods_per_year)
    annual_income = period_gross * periods

    cpp_annual_total, cpp2_annual, cpp_base_annual = _cpp_annual(annual_income, cpp_exempt)
    ei_annual = _ei_annual(annual_income, ei_exempt)

    federal_tax_annual = _federal_tax_annual(
        annual_income=annual_income,
        cpp_base_annual=cpp_base_annual,
        ei_annual=ei_annual,
        basic_personal_amount=federal_basic_personal_amount,
    )
    ontario_tax_annual = _ontario_tax_annual(
        annual_income=annual_income,
        cpp_base_annual=cpp_base_annual,
        ei_annual=ei_annual,
        basic_personal_amount=ontario_basic_personal_amount,
    )

    cpp = _money(cpp_annual_total / periods)
    ei = _money(ei_annual / periods)
    tax = _money((federal_tax_annual + ontario_tax_annual) / periods)
    total_deduction = _money(cpp + ei + tax)
    net = _money(period_gross - total_deduction)

    return {
        "cpp": cpp,
        "ei": ei,
        "tax": tax,
        "total_deduction": total_deduction,
        "net": net,
    }


def _money(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def _weekly_period_number(period_start: date, freq: str) -> int:
    period_anchor = _monday_of_week(period_start)
    first_monday = _first_monday_of_year(period_anchor.year)
    delta_days = max(0, (period_anchor - first_monday).days)
    divisor = 14 if freq == "biweekly" else 7
    return (delta_days // divisor) + 1


def _monday_of_week(value: date) -> date:
    return value - timedelta(days=value.weekday())


def _first_monday_of_year(year: int) -> date:
    jan1 = date(year, 1, 1)
    offset = (7 - jan1.weekday()) % 7
    return jan1 + timedelta(days=offset)


def _apply_brackets(annual_income: Decimal, brackets: list[tuple[Decimal, Decimal, Decimal]]) -> Decimal:
    for limit, rate, constant in brackets:
        if annual_income <= limit:
            return (annual_income * rate) - constant
    return ZERO


def _cpp_annual(annual_income: Decimal, cpp_exempt: bool) -> tuple[Decimal, Decimal, Decimal]:
    if cpp_exempt or annual_income <= ZERO:
        return ZERO, ZERO, ZERO

    pensionable_base = min(annual_income, CPP_YMPE) - CPP_BASIC_EXEMPTION
    if pensionable_base < ZERO:
        pensionable_base = ZERO
    cpp_base = pensionable_base * CPP_BASE_RATE
    cpp_first_additional = pensionable_base * CPP_FIRST_ADDITIONAL_RATE
    cpp_total = cpp_base + cpp_first_additional
    if cpp_total > CPP_MAX_BASE_PLUS:
        cpp_total = CPP_MAX_BASE_PLUS

    cpp2_base = min(annual_income, CPP_YAMPE) - CPP_YMPE
    if cpp2_base < ZERO:
        cpp2_base = ZERO
    cpp2 = cpp2_base * CPP2_RATE
    if cpp2 > CPP2_MAX:
        cpp2 = CPP2_MAX
    return cpp_total + cpp2, cpp2, cpp_base


def _ei_annual(annual_income: Decimal, ei_exempt: bool) -> Decimal:
    if ei_exempt or annual_income <= ZERO:
        return ZERO
    insurable = min(annual_income, EI_MIE)
    ei = insurable * EI_RATE
    if ei > EI_MAX:
        ei = EI_MAX
    return ei


def _federal_tax_annual(
    annual_income: Decimal,
    cpp_base_annual: Decimal,
    ei_annual: Decimal,
    basic_personal_amount: Decimal | None,
) -> Decimal:
    tax_before_credits = _apply_brackets(annual_income, FEDERAL_BRACKETS)
    if tax_before_credits < ZERO:
        tax_before_credits = ZERO
    bpa = basic_personal_amount or FEDERAL_BPA_MAX
    cea = min(FEDERAL_CEA_MAX, annual_income)
    credits_base = bpa + cpp_base_annual + ei_annual + cea
    credits = credits_base * FEDERAL_LOWEST_RATE
    tax_after_credits = tax_before_credits - credits
    return max(tax_after_credits, ZERO)


def _ontario_tax_annual(
    annual_income: Decimal,
    cpp_base_annual: Decimal,
    ei_annual: Decimal,
    basic_personal_amount: Decimal | None,
) -> Decimal:
    tax_before_credits = _apply_brackets(annual_income, ONTARIO_BRACKETS)
    if tax_before_credits < ZERO:
        tax_before_credits = ZERO
    bpa = basic_personal_amount or ONTARIO_BPA
    credits_base = bpa + cpp_base_annual + ei_annual
    credits = credits_base * ONTARIO_LOWEST_RATE
    tax_after_credits = max(tax_before_credits - credits, ZERO)
    surtax = _ontario_surtax(tax_after_credits)
    tax_with_surtax = tax_after_credits + surtax
    health_premium = _ontario_health_premium(annual_income)
    reduction = _ontario_tax_reduction(tax_with_surtax)
    return max(tax_with_surtax + health_premium - reduction, ZERO)


def _ontario_surtax(basic_provincial_tax: Decimal) -> Decimal:
    if basic_provincial_tax <= ONTARIO_SURTAX_THRESHOLD_1:
        return ZERO
    if basic_provincial_tax <= ONTARIO_SURTAX_THRESHOLD_2:
        return (basic_provincial_tax - ONTARIO_SURTAX_THRESHOLD_1) * ONTARIO_SURTAX_RATE_1
    return (
        (basic_provincial_tax - ONTARIO_SURTAX_THRESHOLD_1) * ONTARIO_SURTAX_RATE_1
        + (basic_provincial_tax - ONTARIO_SURTAX_THRESHOLD_2) * ONTARIO_SURTAX_RATE_2
    )


def _ontario_health_premium(annual_income: Decimal) -> Decimal:
    if annual_income <= Decimal("20000"):
        return ZERO
    if annual_income <= Decimal("36000"):
        return min(Decimal("300"), (annual_income - Decimal("20000")) * Decimal("0.06"))
    if annual_income <= Decimal("48000"):
        return min(Decimal("450"), Decimal("300") + (annual_income - Decimal("36000")) * Decimal("0.06"))
    if annual_income <= Decimal("72000"):
        return min(Decimal("600"), Decimal("450") + (annual_income - Decimal("48000")) * Decimal("0.25"))
    if annual_income <= Decimal("200000"):
        return min(Decimal("750"), Decimal("600") + (annual_income - Decimal("72000")) * Decimal("0.25"))
    return min(Decimal("900"), Decimal("750") + (annual_income - Decimal("200000")) * Decimal("0.25"))


def _ontario_tax_reduction(tax_with_surtax: Decimal) -> Decimal:
    reduction_limit = ONTARIO_TAX_REDUCTION_BASIC * 2
    reduction = reduction_limit - tax_with_surtax
    if reduction <= ZERO:
        return ZERO
    if reduction > tax_with_surtax:
        return tax_with_surtax
    return reduction
