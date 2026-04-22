from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base, BaseMixin


class ZMeDB(Base, BaseMixin):
    __tablename__ = "zme"

    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=True)


