from datetime import date, datetime
from decimal import Decimal
from pydantic import AliasChoices, BaseModel, Field
from uuid import UUID
from typing import List, Literal, Optional


class PayrollEntryAddEmployeesRequest(BaseModel):
    """Add employees to the current payroll entry batch."""
    employee_ids: List[UUID] = Field(..., description="Employee IDs to add")

class PayrollEntryCreate(BaseModel):
    """Create a new payroll entry with detailed hours, rates, and deductions."""
    employee_id: UUID = Field(..., description="ID of the employee")
    
    # Hours
    regular_hours: float = Field(..., ge=0, description="Regular hours worked")
    hourly_rate: float = Field(..., ge=0, description="Regular hourly rate")
    
    # Overtime
    overtime_hours: float = Field(default=0, ge=0, description="Overtime hours worked")
    overtime_rate: float = Field(default=0, ge=0, description="Overtime hourly rate")
    
    # Additional earnings
    bonus: float = Field(default=0, ge=0, description="Bonus amount")
    vacation: float = Field(default=0, ge=0, description="Vacation payout")
    
    # Deductions
    cpp: float = Field(default=0, ge=0, description="Canada Pension Plan deduction")
    ei: float = Field(default=0, ge=0, description="Employment Insurance deduction")
    tax: float = Field(default=0, ge=0, description="Income tax deduction")
    
    # Calculated totals
    gross: Decimal = Field(..., description="Gross pay amount")
    total_deduction: Decimal = Field(..., description="Total deductions")
    net: Decimal = Field(..., description="Net pay (gross - deductions)")


class PayrollEntryUpdate(BaseModel):
    """Update a payroll entry. Accepts full row; unset fields are ignored."""
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


class PayrollEntryResponse(BaseModel):
    """Response model for payroll entry with metadata."""
    id: UUID
    payroll_period_id: Optional[UUID] = None
    employee_id: UUID
    full_name: str

    employment_type: str
    annual_salary_snapshot: Optional[Decimal] = None
    hourly_rate_snapshot: Optional[Decimal] = None

    federal_claim_snapshot: Decimal
    ontario_claim_snapshot: Decimal

    regular_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None

    bonus: Decimal 
    vacation: Decimal
    cpp: Decimal 
    ei: Decimal
    tax: Decimal

    gross: Optional[Decimal] = None
    total_deduction: Optional[Decimal] = None
    net: Optional[Decimal] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    period_key: Optional[str] = None

    cpp_exempt_snapshot: bool
    ei_exempt_snapshot: bool
    excluded: bool = Field(default=False)
    status: str = Field(default="draft")
    created_at: datetime

    class Config:
        from_attributes = True


class PayrollEntryFinalizeRequest(BaseModel):
    """Finalize current payroll entries for a schedule."""
    schedule_id: UUID
    pay_day: Optional[date] = None






# --- Payroll Schedule Schemas ---
# class PayrollScheduleCreate(BaseModel):
#     """Create a new payroll schedule."""
#     id: UUID = Field(default_factory=UUID, description="Unique identifier for the payroll schedule")
#     frequency: str = Field(..., description="Payroll frequency (weekly/biweekly/monthly)")
#     effective_from: date = Field(..., description="Date when this schedule becomes effective")
#     effective_to: Optional[date] = Field(None, description="Date when this schedule expires (optional)")
#     status: str = Field(default="active", description="Schedule status (active/inactive)")
#     payon: str = Field(..., description="Day of the week or month when payment is made (e.g., 'Friday' for weekly, '15' for monthly)")
#     semi1: Optional[str] = Field(None, description="For biweekly schedules, the first pay day (e.g., 'Friday')")
#     semi2: Optional[str] = Field(None, description="For biweekly schedules, the second pay day (e.g., 'Friday')")
#     description: Optional[str] = Field(None, description="Optional description of the payroll schedule")


# class PatchSchedule(BaseModel):
#     frequency: Optional[str] = Field(None, description="Payroll frequency (weekly/biweekly/monthly)")
#     anchor_date: Optional[date] = Field(None, description="Anchor date for calculating payroll periods")
#     pay_date_offset_days: Optional[int] = Field(None, ge=0, description="Days after period end when payment is made")
#     effective_from: Optional[date] = Field(None, description="Date when this schedule becomes effective")
#     effective_to: Optional[date] = Field(None, description="Date when this schedule expires (optional)")
#     status: Optional[str] = Field(None, description="Schedule status (active/inactive)")


# class PayrollScheduleResponse(PayrollScheduleCreate):
#     """Response model for payroll schedule with metadata."""
#     created_at: datetime
    
#     class Config:
#         from_attributes = True


# # --- Payroll Period Schemas ---
# class PayrollPeriodCreate(BaseModel):
#     """Create a new payroll period."""
#     payroll_schedule_id: UUID = Field(..., description="ID of the payroll schedule")
#     start_date: date = Field(..., description="Start date of the payroll period")
#     end_date: date = Field(..., description="End date of the payroll period")
#     period_number: int = Field(..., ge=1, description="Sequential number of the period within the schedule")
#     status: Literal["scheduled", "open", "closed"] = Field(
#         default="scheduled",
#         description="Period status (scheduled/open/closed)",
#     )


# class PayrollPeriodGenerateRequest(BaseModel):
#     """Generate payroll periods from a schedule within a requested date range."""
#     payroll_schedule_id: UUID = Field(..., description="ID of the payroll schedule")
#     range_start: date = Field(
#         ...,
#         description="Start date of generation window",
#         validation_alias=AliasChoices("range_start", "start_date"),
#     )
#     range_end: date = Field(
#         ...,
#         description="End date of generation window",
#         validation_alias=AliasChoices("range_end", "end_date"),
#     )
#     starting_period_number: Optional[int] = Field(
#         None,
#         ge=1,
#         description="Optional first period number. If omitted, backend continues from existing periods.",
#     )

#     class Config:
#         populate_by_name = True


# class PayrollPeriodResponse(BaseModel):
#     """Response model for payroll period with metadata."""
#     payroll_schedule_id: UUID
#     start_date: date
#     end_date: date
#     pay_date: date
#     period_number: int
#     id: UUID
#     status: Literal["scheduled", "open", "closed"] = Field(
#         default="scheduled",
#         description="Period status (scheduled/open/closed)",
#     )
#     created_at: datetime
    
#     class Config:
#         from_attributes = True

