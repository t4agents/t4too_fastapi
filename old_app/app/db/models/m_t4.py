# app/db/models/t4.py
from __future__ import annotations
from typing import List, Optional
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from .m_base import Base, BaseMixin


# --- T4 Record ---
class T4Record(Base, BaseMixin):
    __tablename__ = "t4_records"

    employee_id: Mapped[UUID] = mapped_column(ForeignKey("employees.id"), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)

    cra_submission_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("cra_submissions.id"),
        nullable=True
    )

    employment_income: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    cpp_contributions: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    ei_premiums: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    income_tax_deducted: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    other_deductions: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True, default=0)

    cra_submission: Mapped[Optional["CRASubmission"]] = relationship(back_populates="t4_records", uselist=False)


# --- CRA Submission ---
class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"


class CRASubmission(Base, BaseMixin):
    __tablename__ = "cra_submissions"

    company_name: Mapped[str] = mapped_column(String, nullable=False)
    business_number: Mapped[str] = mapped_column(String(9), nullable=False)
    tax_year: Mapped[int] = mapped_column(Integer, nullable=False)

    submitted_date: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True), nullable=True)

    xml_content: Mapped[str] = mapped_column(Text, nullable=False)  # exact XML for auditing

    t4_records: Mapped[List["T4Record"]] = relationship(back_populates="cra_submission")
