from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class EmployeeOut(BaseModel):
    id: UUID
    ten_id: Optional[UUID] = None
    biz_id: Optional[UUID] = None
    usr_id: Optional[UUID] = None
    cli_id: Optional[UUID] = None
    usr_type: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    sin: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    province: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_type: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    annual_salary: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    federal_claim_amount: Optional[Decimal] = None
    ontario_claim_amount: Optional[Decimal] = None
    cpp_exempt: Optional[bool] = None
    ei_exempt: Optional[bool] = None

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


class EmployeeCreate(BaseModel):
    id: Optional[UUID] = None
    ten_id: Optional[UUID] = None
    biz_id: Optional[UUID] = None
    usr_id: Optional[UUID] = None
    cli_id: Optional[UUID] = None
    usr_type: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    sin: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    province: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    employment_type: Optional[str] = None
    hourly_rate: Optional[Decimal] = None
    annual_salary: Optional[Decimal] = None
    regular_hours: Optional[Decimal] = None
    federal_claim_amount: Optional[Decimal] = None
    ontario_claim_amount: Optional[Decimal] = None
    cpp_exempt: Optional[bool] = None
    ei_exempt: Optional[bool] = None

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
