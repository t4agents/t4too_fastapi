from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_ACC, SCHEMA_TOO_GLOBAL
from app.schemas.enu import AccountType, SourceType


class JournalEntryLineDB(Base):
    __tablename__ = "acc_je_lines"
    

    je_header_id: Mapped[UUID] = mapped_column(ForeignKey("acc_je_header.id", ondelete="CASCADE"),index=True)
    je_header = relationship("JournalEntryHeaderDB", back_populates="je_lines")

    coa_id: Mapped[UUID] = mapped_column(ForeignKey("acc_coa.id"),index=True)
    coa = relationship("acc_coa", back_populates="je_lines")

    debit: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    credit: Mapped[float] = mapped_column(Numeric(18, 4), default=0)


    __table_args__ = (
        CheckConstraint("debit >= 0", name="ck_debit_positive"),
        CheckConstraint("credit >= 0", name="ck_credit_positive"),
        CheckConstraint(
            "(debit = 0 AND credit > 0) OR (credit = 0 AND debit > 0)",
            name="ck_one_side_only"
        ),
        Index("ix_jeline_account_date", "account_id"),
        {"schema": SCHEMA_TOO_ACC}
    )