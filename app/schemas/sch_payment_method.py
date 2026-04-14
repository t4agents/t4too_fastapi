from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class PaymentMethodOut(BaseModel):
    id: UUID
    pm_name: Optional[str] = None
    pm_note: Optional[str] = None


class PaymentMethodCreate(BaseModel):
    id: Optional[UUID] = None
    pm_name: Optional[str] = None
    pm_note: Optional[str] = None
