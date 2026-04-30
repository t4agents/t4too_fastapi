from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_ACC, SCHEMA_TOO_GLOBAL
from app.schemas.enu import AccountType



class COADB(Base, BaseMixin):
    __tablename__ = "acc_coa"
    __table_args__ = {"schema": SCHEMA_TOO_ACC}

    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[AccountType] = mapped_column(Enum(AccountType), index=True)

    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("acc_coa.id"), nullable=True
    )

    # parent = relationship("COADB", remote_side=[id], backref="children")