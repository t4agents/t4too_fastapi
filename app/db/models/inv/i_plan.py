from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_INV


class PlanDB(Base, BaseMixin):
    __tablename__ = "iplan"
    __table_args__ = {"schema": SCHEMA_TOO_INV}
    
    plan_code: Mapped[str | None] = mapped_column(String(64))
    plan_name: Mapped[str | None] = mapped_column(String(128))
    plan_price: Mapped[str | None] = mapped_column(String(64))
    plan_features: Mapped[list | None] = mapped_column(JSONB)
