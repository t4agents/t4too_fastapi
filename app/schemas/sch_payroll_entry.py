from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PayrollEntryOut(BaseModel):
    id: UUID
    ten_id: Optional[UUID] = None
    biz_id: Optional[UUID] = None
    usr_id: Optional[UUID] = None
    cli_id: Optional[UUID] = None
    usr_type: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None

    schedule_id: UUID
    payroll_period_id: Optional[UUID] = None
    employee_id: UUID
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    period_key: Optional[str] = None
    pay_date: Optional[date] = None

    employment_type: Optional[str] = None
    full_name: Optional[str] = None
    annual_salary_snapshot: Optional[Decimal] = None
    hourly_rate_snapshot: Optional[Decimal] = None
    federal_claim_snapshot: Optional[Decimal] = None
    ontario_claim_snapshot: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    vacation: Optional[Decimal] = None
    cpp: Optional[Decimal] = None
    ei: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    gross: Optional[Decimal] = None
    total_deduction: Optional[Decimal] = None
    adjustment: Optional[Decimal] = None
    net: Optional[Decimal] = None
    cpp_exempt_snapshot: Optional[bool] = None
    ei_exempt_snapshot: Optional[bool] = None
    excluded: Optional[bool] = None

    b_int: Optional[int] = None
    b_str: Optional[str] = None
    b_decimal: Optional[Decimal] = None
    b_date: Optional[datetime] = None
    b_bool: Optional[bool] = None
    b_json: Optional[Dict[str, Any]] = None

    is_deleted: Optional[bool] = None
    is_flag: Optional[bool] = None
    locale: Optional[str] = None
    status: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class PayrollEntryAddEmployeesRequest(BaseModel):
    employee_ids: list[UUID]


class PayrollEntryUpdate(BaseModel):
    id: UUID
    payroll_period_id: Optional[UUID] = None
    schedule_id: Optional[UUID] = None
    period_key: Optional[str] = None
    employee_id: Optional[UUID] = None
    full_name: Optional[str] = None
    employment_type: Optional[str] = None
    annual_salary_snapshot: Optional[Decimal] = None
    hourly_rate_snapshot: Optional[Decimal] = None
    federal_claim_snapshot: Optional[Decimal] = None
    ontario_claim_snapshot: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    vacation: Optional[Decimal] = None
    cpp: Optional[Decimal] = None
    ei: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    gross: Optional[Decimal] = None
    total_deduction: Optional[Decimal] = None
    adjustment: Optional[Decimal] = None
    net: Optional[Decimal] = None
    cpp_exempt_snapshot: Optional[bool] = None
    ei_exempt_snapshot: Optional[bool] = None
    excluded: Optional[bool] = None
    status: Optional[str] = None


class PayrollFinalizeOut(BaseModel):
    period_key: str
