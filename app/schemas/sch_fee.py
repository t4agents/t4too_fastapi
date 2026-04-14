from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class FeeOut(BaseModel):
    id: UUID
    fee_name: Optional[str] = None
    fee_amount: Optional[float] = None
    fee_note: Optional[str] = None


class FeeCreate(BaseModel):
    id: Optional[UUID] = None
    fee_name: Optional[str] = None
    fee_amount: Optional[float] = None
    fee_note: Optional[str] = None
