from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_AINVOAIC


class FeeDB(Base, BaseMixin):
    __tablename__ = "ifee"
    __table_args__ = {"schema": SCHEMA_TOO_AINVOAIC}


    fee_name: Mapped[str | None] = mapped_column(String(128))
    fee_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    fee_note: Mapped[str | None] = mapped_column(String(1024))

    business = relationship("BusinessEntityDB", back_populates="fee")
