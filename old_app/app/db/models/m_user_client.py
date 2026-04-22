from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base


class UserClient(Base):
    __tablename__ = "user_clients"
    __table_args__ = (
        UniqueConstraint("user_id", "biz_id", name="uq_user_clients_user_biz"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4, index=True)

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    biz_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("biz_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ten_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)

    user = relationship("UserDB", back_populates="user_clients")
    client = relationship("BizEntity", back_populates="user_clients")
