from uuid import UUID

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_AINVOAIC


class PaymentMethodDB(Base, BaseMixin):
    __tablename__ = "ipayment_method"
    __table_args__ = {"schema": SCHEMA_TOO_AINVOAIC}
    
    pm_name: Mapped[str | None] = mapped_column(String(128))
    pm_note: Mapped[str | None] = mapped_column(String(1024))

