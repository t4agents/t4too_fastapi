from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TaxOut(BaseModel):
    id: UUID
    tax_name: Optional[str] = None
    tax_rate: Optional[float] = None
    tax_type: Optional[str] = None
    tax_note: Optional[str] = None


class TaxCreate(BaseModel):
    id: Optional[UUID] = None
    tax_name: Optional[str] = None
    tax_rate: Optional[float] = None
    tax_type: Optional[str] = None
    tax_note: Optional[str] = None
