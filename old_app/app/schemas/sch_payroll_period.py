from datetime import date, datetime
from decimal import Decimal
from pydantic import AliasChoices, BaseModel, Field
from uuid import UUID
from typing import Literal, Optional


# --- Payroll Period Schemas ---
class PayrollPeriodCreate(BaseModel):
    """Create a new payroll period."""
    payroll_schedule_id: UUID = Field(..., description="ID of the payroll schedule")
    start_date: date = Field(..., description="Start date of the payroll period")
    end_date: date = Field(..., description="End date of the payroll period")
    period_number: int = Field(..., ge=1, description="Sequential number of the period within the schedule")
    status: Literal["scheduled", "open", "closed"] = Field(
        default="scheduled",
        description="Period status (scheduled/open/closed)",
    )


class PayrollPeriodGenerateRequest(BaseModel):
    """Generate payroll periods from a schedule within a requested date range."""
    payroll_schedule_id: UUID = Field(..., description="ID of the payroll schedule")
    range_start: date = Field(
        ...,
        description="Start date of generation window",
        validation_alias=AliasChoices("range_start", "start_date"),
    )
    range_end: date = Field(
        ...,
        description="End date of generation window",
        validation_alias=AliasChoices("range_end", "end_date"),
    )
    starting_period_number: Optional[int] = Field(
        None,
        ge=1,
        description="Optional first period number. If omitted, backend continues from existing periods.",
    )

    class Config:
        populate_by_name = True


class PayrollPeriodResponse(BaseModel):
    """Response model for payroll period with metadata."""
    payroll_schedule_id: UUID
    start_date: date
    end_date: date
    pay_date: date
    period_number: int
    id: UUID
    status: Literal["scheduled", "open", "closed"] = Field(
        default="scheduled",
        description="Period status (scheduled/open/closed)",
    )
    created_at: datetime
    
    class Config:
        from_attributes = True


