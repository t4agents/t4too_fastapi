from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime, date


class BizEntityBase(BaseModel):
    type: str = Field(default="FIRM", max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    business_number: Optional[str] = Field(None, max_length=15)
    payroll_account_number: Optional[str] = Field(None, max_length=15)
    province: Optional[str] = Field(default="ON", max_length=2)
    street_address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=7)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    wsib_number: Optional[str] = Field(None, max_length=255)
    eht_account: Optional[str] = Field(None, max_length=255)
    remittance_frequency: Optional[str] = Field(default="monthly")
    tax_year_end: Optional[date] = None
    legal_name: Optional[str] = Field(None, max_length=255)
    operating_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=50)
    incorporation_date: Optional[date] = None
    employee_count: Optional[int] = None


class BizEntityCreate(BizEntityBase):
    pass


class BizEntityUpdate(BaseModel):
    type: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    business_number: Optional[str] = Field(None, max_length=15)
    payroll_account_number: Optional[str] = Field(None, max_length=15)
    province: Optional[str] = Field(None, max_length=2)
    street_address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=255)
    postal_code: Optional[str] = Field(None, max_length=7)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    wsib_number: Optional[str] = Field(None, max_length=255)
    eht_account: Optional[str] = Field(None, max_length=255)
    remittance_frequency: Optional[str] = None
    tax_year_end: Optional[date] = None
    legal_name: Optional[str] = Field(None, max_length=255)
    operating_name: Optional[str] = Field(None, max_length=255)
    business_type: Optional[str] = Field(None, max_length=50)
    incorporation_date: Optional[date] = None
    employee_count: Optional[int] = None


class BizEntityResponse(BizEntityBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
