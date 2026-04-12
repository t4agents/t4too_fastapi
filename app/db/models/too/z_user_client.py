from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.schemas import SCHEMA_TOO_GLOBAL

from .z_base import Base, BaseMixin


class ZUserClientDB(Base, BaseMixin):
    __tablename__ = "zuser_client"
    __table_args__ = (
        UniqueConstraint("usr_id", "biz_id", name="uq_user_client_user_biz"),
        {"schema": SCHEMA_TOO_GLOBAL},
    )

    usr_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_GLOBAL}.zuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    biz_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_GLOBAL}.zbe.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

