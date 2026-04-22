from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class PayrollScheduleOut(BaseModel):
    id: UUID
    ten_id: Optional[UUID] = None
    biz_id: Optional[UUID] = None
    usr_id: Optional[UUID] = None
    cli_id: Optional[UUID] = None
    usr_type: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None

    frequency: Optional[str] = None
    period: Optional[str] = None
    note: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: Optional[str] = None
    payon: Optional[str] = None
    semi1: Optional[str] = None
    semi2: Optional[str] = None

    b_int: Optional[int] = None
    b_str: Optional[str] = None
    b_decimal: Optional[Decimal] = None
    b_date: Optional[datetime] = None
    b_bool: Optional[bool] = None
    b_json: Optional[Dict[str, Any]] = None

    is_deleted: Optional[bool] = None
    is_flag: Optional[bool] = None
    locale: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
