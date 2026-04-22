from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    sin: Optional[str] = Field(
        None,
        min_length=9,
        max_length=9,
        description="Social Insurance Number",
    )
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = None
    province: Optional[str] = Field("ON", max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_type: Optional[str] = Field(None, description="hourly | salary")
    hourly_rate: Optional[Decimal] = None
    overtime_rate: Optional[Decimal] = None
    annual_salary: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    federal_claim_amount: Optional[Decimal] = None
    ontario_claim_amount: Optional[Decimal] = None
    cpp_exempt: Optional[bool] = False
    ei_exempt: Optional[bool] = False


class EmployeeCreate(EmployeeBase):
    payroll_schedule_id: Optional[UUID] = Field(
        None,
        description="ID of the employee's payroll schedule. If omitted, backend picks a default active schedule.",
    )


class EmployeeUpdate(BaseModel):
    id: Optional[UUID] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sin: Optional[str] = Field(None, min_length=9, max_length=9, description="Social Insurance Number")
    date_of_birth: Optional[date] = None
    address: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = None
    province: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_type: Optional[str] = Field(None, description="hourly | salary | contract | seasonal | other")
    hourly_rate: Optional[Decimal] = None
    annual_salary: Optional[Decimal] = None
    federal_claim_amount: Optional[Decimal] = None
    ontario_claim_amount: Optional[Decimal] = None
    cpp_exempt: Optional[bool] = None
    ei_exempt: Optional[bool] = None
    is_deleted: Optional[bool] = None
    payroll_schedule_id: Optional[UUID] = Field(None, description="ID of the employee's payroll schedule")


class EmployeeResponse(EmployeeBase):
    id: UUID
    payroll_schedule_id: Optional[UUID] = Field(None, description="ID of the employee's payroll schedule")
    biz_id: Optional[UUID] = Field(None, description="Business entity ID")
    created_at: datetime

    class Config:
        from_attributes = True


class EmployeePayrollScheduleOption(BaseModel):
    id: UUID
    label: str


class EmployeeFormOptionsResponse(BaseModel):
    payroll_schedules: list[EmployeePayrollScheduleOption]
    default_payroll_schedule_id: Optional[UUID] = None
