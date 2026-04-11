from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.schemas import SCHEMA_TOO_GLOBAL

from .z_base import Base


class ZUserClientDB(Base):
    __tablename__ = "zuser_clients"
    __table_args__ = {"schema": SCHEMA_TOO_GLOBAL}
    __table_args__ = (UniqueConstraint("usr_id", "biz_id", name="uq_user_clients_user_biz"),)

    usr_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("zuser.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    biz_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("zbe.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # user = relationship("UserDB", back_populates="user_clients")
    # client = relationship("BizEntity", back_populates="user_clients")
