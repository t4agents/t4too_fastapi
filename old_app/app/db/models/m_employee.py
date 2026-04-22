# --- Employee (payroll-ready minimal version) ---
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (Computed, ForeignKey,String,Numeric,Date,Boolean, Uuid,)
from sqlalchemy.orm import Mapped, mapped_column

from .m_base import Base, BaseMixin


class Employee(Base, BaseMixin):
    __tablename__ = "employees"

    # --- Identity ---
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, Computed("first_name || ' ' || last_name", persisted=True))
    sin: Mapped[str] = mapped_column(String(9), nullable=True )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)

    # --- Contact ---
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    province: Mapped[str] = mapped_column(String(20), nullable=True, default="ON")

    # --- Employment ---
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_type: Mapped[str] = mapped_column(String, nullable=True)  # "hourly" | "salary" | "contract" | "seasonal"| "other"

    hourly_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    annual_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    
    regular_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # --- TD1 Totals (store final claim amounts only) ---
    federal_claim_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    ontario_claim_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)

    # --- CPP / EI Flags ---
    cpp_exempt: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    ei_exempt: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
