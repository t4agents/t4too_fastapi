from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime
from decimal import Decimal


class InvoiceBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    status: str = Field(default="pending", pattern="^(paid|pending|overdue)$")


class InvoiceCreate(InvoiceBase):
    due_date: Optional[datetime] = Field(None)


class InvoiceResponse(InvoiceBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
