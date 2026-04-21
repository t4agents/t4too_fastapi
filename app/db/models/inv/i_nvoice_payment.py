from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas.schemas import SCHEMA_TOO_INV


class InvoicePaymentDB(Base, BaseMixin):
    __tablename__ = "invoice_payment"
    __table_args__ = {"schema": SCHEMA_TOO_INV}

    inv_id: Mapped[UUID] = mapped_column(Uuid, index=True)

    pm_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        nullable=True,
    )
    pm_name: Mapped[str | None] = mapped_column(String(128))
    pm_note: Mapped[str | None] = mapped_column(String(1024))

    pay_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pay_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    pay_reference: Mapped[str | None] = mapped_column(String(256))
    pay_note: Mapped[str | None] = mapped_column(String(1024))

