from __future__ import annotations
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Numeric, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from .m_base import Base, BaseMixin


class InvoiceStatus(str, enum.Enum):
    paid = "paid"
    pending = "pending"
    overdue = "overdue"


class Invoice(Base, BaseMixin):
    __tablename__ = "invoices"

    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.pending,
        nullable=False
    )
    due_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)
