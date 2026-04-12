from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import Uuid

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_AI

class AICacheDB(Base, BaseMixin):
    __tablename__ = "ai_cache"
    __table_args__ = (UniqueConstraint("ten_id", "cache_key", name="uq_agent_cache_ten_key"),
        {"schema": SCHEMA_TOO_AI},)

    cache_key: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
