from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Identity, Numeric, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_ACC


class COADB(Base, BaseMixin):
    __tablename__ = "coa"
    __table_args__ = (
        UniqueConstraint("ten_id", "code", name="uq_accounts_owner_code"),
        CheckConstraint(
            "type in ('asset','liability','equity','revenue','expense')",
            name="ck_accounts_type",
        ),
        {"schema": SCHEMA_TOO_ACC}
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    subtype: Mapped[str | None] = mapped_column(String(100), nullable=True)


class TransactionRawDB(Base, BaseMixin):
    __tablename__ = "transactions_raw"
    __table_args__ = (
        UniqueConstraint("ten_id", "hash", name="uq_transactions_owner_hash"),
        CheckConstraint(
            "status in ('new','mapped','needs_review','posted')",
            name="ck_transactions_raw_status",
        ),
            {"schema": SCHEMA_TOO_ACC}
    )

    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'csv'"))
    source_file_name: Mapped[str | None] = mapped_column(String(255))
    external_id: Mapped[str | None] = mapped_column(String(255))
    txn_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default=text("'CAD'"))
    hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'new'"))


class JeDraftDB(Base, BaseMixin):
    __tablename__ = "je_drafts"
    __table_args__ = (
        CheckConstraint("confidence >= 0 and confidence <= 1", name="ck_je_drafts_confidence"),
        {"schema": SCHEMA_TOO_ACC}
    )

    transaction_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_ACC}.transactions_raw.id", ondelete="SET NULL"),
        nullable=True,
    )
    ai_model: Mapped[str] = mapped_column(String(120), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved: Mapped[bool | None] = mapped_column(nullable=True)
    approved_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class JeDraftLineDB(Base, BaseMixin):
    __tablename__ = "je_draft_lines"
    __table_args__ = (
        CheckConstraint("line_type in ('debit','credit')", name="ck_je_draft_lines_line_type"),
        CheckConstraint("amount > 0", name="ck_je_draft_lines_amount_positive"),
            {"schema": SCHEMA_TOO_ACC}
    )

    draft_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_ACC}.je_drafts.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{SCHEMA_TOO_ACC}.coa.id", ondelete="RESTRICT"), nullable=False
    )
    line_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class JournalEntryDB(Base, BaseMixin):
    __tablename__ = "journal_entries"
    __table_args__ = (
        CheckConstraint("source in ('manual','ai','import','reversal')", name="ck_journal_entries_source"),
        UniqueConstraint("ten_id", "entry_no", name="uq_journal_entries_owner_entry_no"),
        {"schema": SCHEMA_TOO_ACC}
    )

    entry_no: Mapped[int] = mapped_column(Identity(always=True), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'manual'"))
    source_ref_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    posted_by: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    posted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    period_yyyymm: Mapped[int] = mapped_column(nullable=False)
    is_reversal: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    reversed_entry_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_ACC}.journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )


class JournalEntryLine(Base, BaseMixin):
    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        CheckConstraint("line_type in ('debit','credit')", name="ck_journal_entry_lines_line_type"),
        CheckConstraint("amount > 0", name="ck_journal_entry_lines_amount_positive"),
        {"schema": SCHEMA_TOO_ACC}
    )

    journal_entry_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_ACC}.journal_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey(f"{SCHEMA_TOO_ACC}.coa.id", ondelete="RESTRICT"), nullable=False
    )
    line_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


class PeriodCloseDB(Base, BaseMixin):
    __tablename__ = "period_closes"
    __table_args__ = (UniqueConstraint("ten_id", "period_yyyymm", name="uq_period_closes_owner_period"), {"schema": SCHEMA_TOO_ACC})

    period_yyyymm: Mapped[int] = mapped_column(nullable=False)
    is_closed: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)


class AuditEventDB(Base, BaseMixin):
    __tablename__ = "audit_events"
    __table_args__ = {"schema": SCHEMA_TOO_ACC}

    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
