from sqlalchemy import  Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_INV


class FeeDB(Base, BaseMixin):
    __tablename__ = "ifee"
    __table_args__ = {"schema": SCHEMA_TOO_INV}


    fee_name: Mapped[str | None] = mapped_column(String(128))
    fee_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    fee_note: Mapped[str | None] = mapped_column(String(1024))

