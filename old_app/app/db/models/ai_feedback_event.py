from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Text, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid

from app.db.models.m_base import Base


class FeedbackEventDB(Base):
    __tablename__ = "ai_feedback_event"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    ten_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    biz_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    user_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    session_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)
    message_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True, index=True)

    route: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    model: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)

    feedback_type: Mapped[str | None] = mapped_column(Text, nullable=True, index=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
