from datetime import date

from sqlalchemy import ForeignKey, Numeric, String, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_T4AGENTS

class PayrollScheduleDB(Base, BaseMixin):
    __tablename__ = "payroll_schedules"
    __table_args__ = {"schema": SCHEMA_TOO_T4AGENTS}

    frequency: Mapped[str] = mapped_column(String, nullable=False, default="monthly")
    period: Mapped[str] = mapped_column(String, nullable=False, default="Mon-Fri")
    note: Mapped[str] = mapped_column(String, nullable=False, default="Note")

    effective_from: Mapped[date] = mapped_column(nullable=False, default=date.today)
    effective_to: Mapped[date] = mapped_column(nullable=False, default=date.max)

    status: Mapped[str] = mapped_column(String, nullable=False, default="inactive")

    payon: Mapped[str] = mapped_column(String, nullable=False, default="Friday")
    semi1: Mapped[str] = mapped_column(String, nullable=False, default="EOM")
    semi2: Mapped[str] = mapped_column(String, nullable=False, default="EOM")