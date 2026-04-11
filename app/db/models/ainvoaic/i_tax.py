from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas import SCHEMA_TOO_AINVOAIC


class TaxDB(Base, BaseMixin):
    __tablename__ = "taxes"
    __table_args__ = {"schema": SCHEMA_TOO_AINVOAIC}

    tax_name: Mapped[str | None] = mapped_column(String(128))
    tax_rate: Mapped[float | None] = mapped_column(Numeric(8, 4))
    tax_type: Mapped[str | None] = mapped_column(String(64))
    tax_note: Mapped[str | None] = mapped_column(String(1024))

