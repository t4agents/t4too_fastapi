from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional
from datetime import datetime, date


class BizEntityBase(BaseModel):
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None
    type: str = Field(default="FIRM", max_length=50)
    name: str = Field(default="Toronto Blue Jays", min_length=1, max_length=255)
    business_number: Optional[str] = Field(default="888866689RP0001", max_length=15)  # CRA business number format: 9 digits + RP + 4 digits
    payroll_account_number: Optional[str] = Field(default="999986689RP0001", max_length=15)  # Often same as business number for payroll
    province: Optional[str] = Field(default="ON", max_length=2)
    street_address: Optional[str] = Field(default="100 King Street West", max_length=500)
    city: Optional[str] = Field(default="Toronto", max_length=255)
    postal_code: Optional[str] = Field(default="M5X 1A9", max_length=7)  # Toronto financial district
    phone: Optional[str] = Field(default="416-555-0123", max_length=20)  # Toronto area code
    email: Optional[str] = Field(default="info@company.ca", max_length=255)
    wsib_number: Optional[str] = Field(default="8239567A", max_length=255)  # WSIB format: 7 digits + letter
    eht_account: Optional[str] = Field(default="9238567890", max_length=255)  # EHT account number
    remittance_frequency: Optional[str] = Field(default="Monthly")
    tax_year_end: Optional[date] = Field(default=date(2025, 12, 31))  # Typical calendar year end
    legal_name: Optional[str] = Field(default="Toronto Blue Jays", max_length=255)  # Corporation number format
    operating_name: Optional[str] = Field(default="Toronto Blue Jays", max_length=255)
    business_type: Optional[str] = Field(default="Corporation", max_length=50)
    incorporation_date: Optional[date] = Field(default=date(2020, 1, 15))
    employee_count: Optional[int] = Field(default=25)
    
    model_config = ConfigDict(from_attributes=True)

class BizEntityCreate(BizEntityBase):
    pass

class BizEntityUpdate(BizEntityBase):
    pass

class BizEntityResponse(BizEntityBase):
    # Response model may include existing records with empty names, so relax validation here
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


