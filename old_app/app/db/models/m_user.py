from sqlalchemy import UUID, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base, BaseMixin


class UserDB(Base, BaseMixin):
    __tablename__ = "users"

    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=True)
    # active_biz_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=True)

    

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=True)
    last_name: Mapped[str] = mapped_column(String, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=True)        # Full name for display purposes
    avatar: Mapped[str] = mapped_column(String, nullable=True)        # Full name for display purposes
    phone: Mapped[str] = mapped_column(String, nullable=True)
    position: Mapped[str] = mapped_column(String, nullable=True)

    # Social links
    facebook: Mapped[str] = mapped_column(String, nullable=True)
    twitter: Mapped[str] = mapped_column(String, nullable=True)
    github: Mapped[str] = mapped_column(String, nullable=True)
    reddit: Mapped[str] = mapped_column(String, nullable=True)

    # Address details
    country: Mapped[str] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, nullable=True)
    pin: Mapped[str] = mapped_column(String, nullable=True)
    zip: Mapped[str] = mapped_column(String, nullable=True)
    tax_no: Mapped[str] = mapped_column(String, nullable=True)

    role: Mapped[str] = mapped_column(String, nullable=True, default="owner")
    group: Mapped[str] = mapped_column(String, nullable=True, default="coregroup")

    user_clients = relationship("UserClient", back_populates="user", cascade="all, delete-orphan")
