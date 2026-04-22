from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base, BaseMixin


# =========================
# Payroll Schedule
# =========================

class PayrollSchedule(Base, BaseMixin):
    __tablename__ = "payroll_schedules"

    frequency: Mapped[str] = mapped_column(String, nullable=False)

    anchor_date: Mapped[date] = mapped_column(nullable=False)
    pay_date_offset_days: Mapped[int] = mapped_column(nullable=False)

    effective_from: Mapped[date] = mapped_column(nullable=False)
    effective_to: Mapped[Optional[date]]

    status: Mapped[str] = mapped_column(String, default="active")


# =========================
# Payroll Period
# =========================

class PayrollPeriod(Base, BaseMixin):
    __tablename__ = "payroll_periods"

    __table_args__ = (
        UniqueConstraint(
            "payroll_schedule_id",
            "start_date",
            name="uq_schedule_start_date",
        ),
    )

    payroll_schedule_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_schedules.id"),
        nullable=False,
        index=True,
    )

    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    pay_date: Mapped[date] = mapped_column(nullable=False)

    status: Mapped[str] = mapped_column(String, default="in_progress")


# =========================
# Payroll Entry
# =========================

class PayrollEntry(Base, BaseMixin):
    __tablename__ = "payroll_entries"

    __table_args__ = (
        UniqueConstraint(
            "payroll_period_id",
            "employee_id",
            name="uq_period_employee",
        ),
    )

    payroll_period_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_periods.id"),
        nullable=False,
        index=True,
    )

    employee_id: Mapped[UUID] = mapped_column(
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    # Hours
    regular_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Rates
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    overtime_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Earnings
    bonus: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    vacation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Deductions
    cpp: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    ei: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Totals
    gross: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    total_deduction: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)
    net: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=True)

    status: Mapped[str] = mapped_column(String, default="in_progress")
