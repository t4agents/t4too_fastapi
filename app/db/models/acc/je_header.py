from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_ACC, SCHEMA_TOO_GLOBAL
from app.schemas.enu import AccountType, SourceType


class JournalEntryHeaderDB(Base):
    __tablename__ = "acc_je_header"
    __table_args__ = {"schema": SCHEMA_TOO_ACC}

    je_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    je_description: Mapped[str | None] = mapped_column(Text)

    je_source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    je_source_id: Mapped[UUID | None] = mapped_column(nullable=True)

    je_posted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    je_lines = relationship(
        "JournalEntryLineDB",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
    )