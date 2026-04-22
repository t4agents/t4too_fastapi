from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field



class HistoryListRow(BaseModel):
    period_key: str
    schedule_id: UUID
    period_start: date
    period_end: date
    pay_day: Optional[date] = None

    status: str

    total_gross: Decimal
    payroll_cost: Decimal
    total_net: Decimal
    taxes_and_deductions: Decimal
    employee_count: int
    excluded_count: int


class PayrollHistoryFinalizeRequest(BaseModel):
    schedule_id: UUID
    period_start: date
    period_end: date
    period_key: str
    pay_day: Optional[date] = None


class PayrollHistoryEntryResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    employee_id: UUID
    period_key: str
    full_name: Optional[str] = None
    employment_type: Optional[str] = None

    annual_salary_snapshot: Optional[Decimal] = None
    hourly_rate_snapshot: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    bonus: Decimal
    vacation: Decimal
    adjustment: Optional[Decimal] = None

    cpp: Decimal
    ei: Decimal
    tax: Decimal
    gross: Optional[Decimal] = None
    total_deduction: Optional[Decimal] = None
    net: Optional[Decimal] = None
    excluded: Optional[bool] = None
    status: str

    class Config:
        from_attributes = True



class HistoryDetailResponse(BaseModel):
    summary: HistoryListRow
    entries: List[PayrollHistoryEntryResponse]
