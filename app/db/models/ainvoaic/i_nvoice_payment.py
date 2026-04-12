from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas import SCHEMA_TOO_AINVOAIC


class InvoicePaymentDB(Base, BaseMixin):
    __tablename__ = "invoice_payment"
    __table_args__ = {"schema": SCHEMA_TOO_AINVOAIC}

    inv_id: Mapped[UUID] = mapped_column(        Uuid,        ForeignKey(f"{SCHEMA_TOO_AINVOAIC}.invoice.id"),        index=True,    )

    pm_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey(f"{SCHEMA_TOO_AINVOAIC}.i_payment_method.id"),
        nullable=True,
    )
    pm_name: Mapped[str | None] = mapped_column(String(128))
    pm_note: Mapped[str | None] = mapped_column(String(1024))

    pay_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pay_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    pay_reference: Mapped[str | None] = mapped_column(String(256))
    pay_note: Mapped[str | None] = mapped_column(String(1024))

    invoice = relationship("InvoiceDB", back_populates="payments")
