from datetime import date, datetime
from decimal import Decimal
from pydantic import AliasChoices, BaseModel, Field
from uuid import UUID
from typing import Literal, Optional


# --- Payroll Schedule Schemas ---
class ScheduleBase(BaseModel):
    """Create a new payroll schedule."""
    id: UUID = Field(default_factory=UUID, description="Unique identifier for the payroll schedule")
    frequency: str = Field("monthly", description="Payroll frequency (weekly/biweekly/monthly)")
    period: str = Field("Mon-Fri", description="Payroll period (e.g., '1-15', '16-31' for semi-monthly)")
    payon: str = Field("Friday", description="Payment day (e.g., 'last day of month', '15th of month')")
    semi1: str = Field("EOM", description="First semi-monthly period (e.g., '1-15')")
    semi2: str = Field("EOM", description="Second semi-monthly period (e.g., '16-31')")
    effective_from: date = Field(date.today(), description="Date when this schedule becomes effective")
    status: str = Field(default="active", description="Schedule status (active/inactive)")
    note: str = Field(default="Additional notes about the payroll schedule")
    class Config:
        from_attributes = True


# --- Payroll Schedule Schemas ---
class PayrollScheduleCreate(BaseModel):
    """Create a new payroll schedule."""
    id: UUID = Field(default_factory=UUID, description="Unique identifier for the payroll schedule")
    frequency: str = Field(..., description="Payroll frequency (weekly/biweekly/monthly)")
    effective_from: date = Field(..., description="Date when this schedule becomes effective")
    effective_to: Optional[date] = Field(None, description="Date when this schedule expires (optional)")
    status: str = Field(default="active", description="Schedule status (active/inactive)")
    payon: str = Field(..., description="Day of the week or month when payment is made (e.g., 'Friday' for weekly, '15' for monthly)")
    semi1: Optional[str] = Field(None, description="For biweekly schedules, the first pay day (e.g., 'Friday')")
    semi2: Optional[str] = Field(None, description="For biweekly schedules, the second pay day (e.g., 'Friday')")
    description: Optional[str] = Field(None, description="Optional description of the payroll schedule")


class PatchSchedule(BaseModel):
    frequency: Optional[str] = Field(None, description="Payroll frequency (weekly/biweekly/monthly)")
    anchor_date: Optional[date] = Field(None, description="Anchor date for calculating payroll periods")
    effective_from: Optional[date] = Field(None, description="Date when this schedule becomes effective")
    effective_to: Optional[date] = Field(None, description="Date when this schedule expires (optional)")
    status: Optional[str] = Field(None, description="Schedule status (active/inactive)")


class PayrollScheduleResponse(PayrollScheduleCreate):
    """Response model for payroll schedule with metadata."""
    created_at: datetime
    
    class Config:
        from_attributes = True


