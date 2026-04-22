from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


# --- Payroll Schedule Schemas ---
class PayrollScheduleCreate(BaseModel):
    """Create a new payroll schedule."""
    frequency: str = Field(..., description="Payroll frequency (weekly/biweekly/monthly)")
    anchor_date: date = Field(..., description="Anchor date for calculating payroll periods")
    pay_date_offset_days: int = Field(..., ge=0, description="Days after period end when payment is made")
    effective_from: date = Field(..., description="Date when this schedule becomes effective")
    effective_to: Optional[date] = Field(None, description="Date when this schedule expires (optional)")


class PayrollScheduleResponse(PayrollScheduleCreate):
    """Response model for payroll schedule with metadata."""
    id: UUID
    status: str = Field(default="active", description="Schedule status (active/inactive)")
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Payroll Period Schemas ---
class PayrollPeriodCreate(BaseModel):
    """Create a new payroll period."""
    payroll_schedule_id: UUID = Field(..., description="ID of the payroll schedule")
    start_date: date = Field(..., description="Start date of the payroll period")
    end_date: date = Field(..., description="End date of the payroll period")
    pay_date: date = Field(..., description="Date when employees are paid")


class PayrollPeriodResponse(PayrollPeriodCreate):
    """Response model for payroll period with metadata."""
    id: UUID
    status: str = Field(default="in_progress", description="Period status (in_progress/finalized)")
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Payroll Entry Schemas ---
class PayrollEntryCreate(BaseModel):
    """Create a new payroll entry with detailed hours, rates, and deductions."""
    payroll_period_id: UUID = Field(..., description="ID of the payroll period")
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


class PayrollEntryResponse(PayrollEntryCreate):
    """Response model for payroll entry with metadata."""
    id: UUID
    status: str = Field(default="in_progress", description="Entry status (in_progress/completed)")
    created_at: datetime
    
    class Config:
        from_attributes = True