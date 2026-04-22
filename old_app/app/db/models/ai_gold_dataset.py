from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import DateTime, Text, Integer, Boolean, func
from sqlalchemy import Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.m_base import Base
from sqlalchemy import Uuid


class RAGEvalDatasetDB(Base):
    __tablename__ = "rag_eval_dataset"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # question
    question: Mapped[str] = mapped_column(Text, nullable=False)

    # expected answer (ground truth)
    expected_answer: Mapped[str] = mapped_column(Text, nullable=False)

    # list of relevant source_ids (UUIDs from your payroll_history_384)
    relevant_source_ids: Mapped[list[str]
                                ] = mapped_column(JSONB, nullable=False)

    # optional: difficulty / category
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # active flag (for versioning / filtering)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class RAGEvalResultDB(Base):
    __tablename__ = "rag_eval_result"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    dataset_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("rag_eval_dataset.id"),
        nullable=False,
        index=True
    )
    run_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("rag_eval_run.id"),
        nullable=True,
        index=True
    )

    # what system returned
    retrieved_source_ids: Mapped[list[str]
                                 ] = mapped_column(JSONB, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # metrics
    recall_at_k: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True)
    precision_at_k: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_faithful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # optional: raw scoring (LLM judge output)
    eval_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class RAGEvalRunDB(Base):
    __tablename__ = "rag_eval_run"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)

    # versioning
    embedding_version: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)

    # metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
