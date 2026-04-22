from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Text, Integer, Boolean, Numeric, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid

from app.db.models.m_base import Base


class GuardrailEventDB(Base):
    __tablename__ = "ai_guardrail_event"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ten_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    biz_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    route: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    judge_model: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_hallucination: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_refusal: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_fallback: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    latency_ms: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)

    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
