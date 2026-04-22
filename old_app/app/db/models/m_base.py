# app/db/base.py
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.sql import func

class Base(DeclarativeBase): pass

class BaseMixin:
    id: Mapped[UUID] = mapped_column(Uuid,primary_key=True,default=uuid4, index=True)
    ten_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=True)
    biz_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=True)
    owner_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=True)

    b_int: Mapped[int] = mapped_column(Integer, default=1,nullable=True)
    b_str: Mapped[str] = mapped_column(String, default="active",nullable=True)
    b_decimal: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    b_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    b_bool: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    b_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(MutableDict.as_mutable(JSONB),nullable=True,)

    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)
    is_flag:    Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    status: Mapped[str] = mapped_column(String, default="active", nullable=True)
    type:   Mapped[str] = mapped_column(String, default="mytype", nullable=True)
    description: Mapped[str] = mapped_column(String,default="description",nullable=True)

