from uuid import UUID

from sqlalchemy import ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.too.z_base import Base, BaseMixin
from app.db.schemas import SCHEMA_TOO_AINVOAIC


class InvoiceItemDB(Base, BaseMixin):
    __tablename__ = "invoice_item"
    __table_args__ = {"schema": SCHEMA_TOO_AINVOAIC}

    inv_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("invoice.id"), index=True)

    item_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("item.id"), nullable=True)
    item_number: Mapped[str | None] = mapped_column(String(64))
    item_name: Mapped[str | None] = mapped_column(String(256))
    item_rate: Mapped[float | None] = mapped_column(Numeric(12, 2))
    item_unit_of_measure: Mapped[str | None] = mapped_column(String(64))
    item_unit: Mapped[str | None] = mapped_column(String(64))
    item_sku: Mapped[str | None] = mapped_column(String(128))
    item_description: Mapped[str | None] = mapped_column(String(1024))

    item_quantity: Mapped[int | None] = mapped_column(Integer)
    item_note: Mapped[str | None] = mapped_column(String(1024))
    item_amount: Mapped[float | None] = mapped_column(Numeric(12, 2))

    invoice = relationship("InvoiceDB", back_populates="items")
