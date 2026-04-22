
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base, BaseMixin


# =========================
# Payroll Entry
# =========================
from sqlalchemy import Boolean


class PayrollEntry(Base, BaseMixin):
    __tablename__ = "payroll_entries"

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey("payroll_schedules.id"), nullable=False, index=True,)
    payroll_period_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payroll_periods.id"),
        nullable=True,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True,)

    period_start: Mapped[Optional[date]] = mapped_column(nullable=True, index=True)
    period_end: Mapped[Optional[date]] = mapped_column(nullable=True, index=True)
    period_key: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    pay_date: Mapped[Optional[date]] = mapped_column(nullable=True, index=True)

    # --- Snapshot Employment Type ---
    employment_type: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    annual_salary_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    hourly_rate_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # --- Snapshot TD1 ---
    federal_claim_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ontario_claim_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # --- Hours (nullable for salary) ---
    regular_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    overtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    

    # --- Extra Earnings ---
    bonus: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    vacation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # --- Deductions ---
    cpp: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    ei: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # --- Totals ---
    gross: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_deduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    adjustment: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    net: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    cpp_exempt_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ei_exempt_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # --- Control ---
    excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String, default="draft", nullable=False)
