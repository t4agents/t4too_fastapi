from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ItemOut(BaseModel):
    id: UUID
    item_number: Optional[str] = None
    item_name: Optional[str] = None
    item_rate: Optional[float] = None
    item_unit_of_measure: Optional[str] = None
    item_unit: Optional[str] = None
    item_sku: Optional[str] = None
    item_description: Optional[str] = None
    item_quantity: Optional[int] = None
    item_note: Optional[str] = None
    item_amount: Optional[float] = None


class ItemCreate(BaseModel):
    id: Optional[UUID] = None
    item_number: Optional[str] = None
    item_name: Optional[str] = None
    item_rate: Optional[float] = None
    item_unit_of_measure: Optional[str] = None
    item_unit: Optional[str] = None
    item_sku: Optional[str] = None
    item_description: Optional[str] = None
    item_quantity: Optional[int] = None
    item_note: Optional[str] = None
    item_amount: Optional[float] = None
