from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from typing import Optional
from datetime import datetime

class MyUserBase(BaseModel):
    firebase_uid: Optional[str] = Field(None, max_length=128)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    avatar: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=255)
    facebook: Optional[str] = Field(None, max_length=255)
    twitter: Optional[str] = Field(None, max_length=255)
    github: Optional[str] = Field(None, max_length=255)
    reddit: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    pin: Optional[str] = Field(None, max_length=10)
    zip: Optional[str] = Field(None, max_length=10)
    tax_no: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(default="owner", max_length=50)
    group: Optional[str] = Field(default="coregroup", max_length=50)


class MyUserCreate(MyUserBase):
    pass


class MyUserUpdate(BaseModel):
    firebase_uid: Optional[str] = Field(None, max_length=128)
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    name: Optional[str] = Field(None, max_length=255)
    avatar: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    position: Optional[str] = Field(None, max_length=255)
    facebook: Optional[str] = Field(None, max_length=255)
    twitter: Optional[str] = Field(None, max_length=255)
    github: Optional[str] = Field(None, max_length=255)
    reddit: Optional[str] = Field(None, max_length=255)
    country: Optional[str] = Field(None, max_length=255)
    state: Optional[str] = Field(None, max_length=255)
    pin: Optional[str] = Field(None, max_length=10)
    zip: Optional[str] = Field(None, max_length=10)
    tax_no: Optional[str] = Field(None, max_length=50)
    role: Optional[str] = Field(None, max_length=50)
    group: Optional[str] = Field(None, max_length=50)


class MyUserResponse(MyUserBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True