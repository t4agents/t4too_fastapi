from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import Uuid

from .m_base import Base


class AgentCache(Base):
    __tablename__ = "agent_cache"
    __table_args__ = (
        UniqueConstraint("ten_id", "cache_key", name="uq_agent_cache_ten_key"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4, index=True)
    ten_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    biz_id: Mapped[UUID | None] = mapped_column(Uuid, index=True, nullable=True)
    cache_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
