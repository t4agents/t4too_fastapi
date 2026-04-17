from typing import Optional

from pydantic import BaseModel


class UserProfileOut(BaseModel):
    email: str
    display_name: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    tax_no: Optional[str] = None
    note: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    plan_type: Optional[str] = None
    avatar: Optional[str] = None


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    tax_no: Optional[str] = None
    note: Optional[str] = None
    position: Optional[str] = None
    country: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    plan_type: Optional[str] = None
    avatar: Optional[str] = None
