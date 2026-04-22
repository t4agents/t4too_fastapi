from datetime import date
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .m_base import Base, BaseMixin


class PayrollPeriod(Base, BaseMixin):
    __tablename__ = "payroll_periods"
    __table_args__ = (
        UniqueConstraint(
            "biz_id",
            "period_key",
            name="uq_payroll_period_key",
        ),
    )

    payroll_schedule_id: Mapped[UUID] = mapped_column(
        ForeignKey("payroll_schedules.id"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    pay_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    period_key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="open")
