from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_T4


class PayrollHistoryDB(Base, BaseMixin):
    __tablename__ = "payroll_history"
    __table_args__ = {"schema": SCHEMA_TOO_T4}

    schedule_id: Mapped[UUID] = mapped_column(ForeignKey(f"{SCHEMA_TOO_T4}.payroll_schedules.id"), nullable=False, index=True)
    payroll_period_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{SCHEMA_TOO_T4}.payroll_periods.id"),
        nullable=True,
        index=True,
    )
    employee_id: Mapped[UUID] = mapped_column(ForeignKey(f"{SCHEMA_TOO_T4}.employees.id"), nullable=False, index=True)

    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pay_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    employment_type: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String, nullable=True)
    annual_salary_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    hourly_rate_snapshot: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    federal_claim_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ontario_claim_snapshot: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    regular_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    overtime_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    bonus: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    vacation: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    cpp: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    ei: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    gross: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    total_deduction: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    adjustment: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    net: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    cpp_exempt_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ei_exempt_snapshot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    excluded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String, default="finalized", nullable=False)
