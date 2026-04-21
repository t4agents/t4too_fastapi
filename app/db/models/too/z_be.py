from datetime import datetime

from sqlalchemy import UUID, Boolean, Date, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.schemas.schemas import SCHEMA_TOO_INV, SCHEMA_TOO_GLOBAL

from .z_base import Base, BaseMixin


class ZBizEntityDB(Base, BaseMixin):
    __tablename__ = "zbe"
    __table_args__ = {"schema": SCHEMA_TOO_GLOBAL}

    be_type: Mapped[str] = mapped_column(String, nullable=False, default="FIRM")
    be_name: Mapped[str] = mapped_column(String, nullable=False, default="my org")
    be_logo: Mapped[str | None] = mapped_column(String(512))
    be_contact: Mapped[str | None] = mapped_column(String(128))
    be_contact_title: Mapped[str | None] = mapped_column(String(128))
    be_address: Mapped[str | None] = mapped_column(String(512))
    be_email: Mapped[str | None] = mapped_column(String(128))
    be_phone: Mapped[str | None] = mapped_column(String(64))
    be_website: Mapped[str | None] = mapped_column(String(256))

    be_biz_number: Mapped[str | None] = mapped_column(String(128))
    be_tax_id: Mapped[str | None] = mapped_column(String(128))
    be_bank_info: Mapped[str | None] = mapped_column(String(1024))
    be_payment_term: Mapped[int | None] = mapped_column(Integer)

    be_currency: Mapped[str | None] = mapped_column(String(16))
    be_inv_template_id: Mapped[str | None] = mapped_column(String(32))
    be_description: Mapped[str | None] = mapped_column(String(1024))
    be_note: Mapped[str | None] = mapped_column(String(1024))

    be_timezone: Mapped[str | None] = mapped_column(String(64))
    be_date_format: Mapped[str | None] = mapped_column(String(32))
    be_inv_prefix: Mapped[str | None] = mapped_column(String(32))
    be_inv_integer: Mapped[int | None] = mapped_column(Integer)
    be_inv_integer_max: Mapped[int | None] = mapped_column(Integer)

    be_show_paid_stamp: Mapped[bool | None] = mapped_column(Boolean, default=True)

    be_plan_id: Mapped[UUID | None] = mapped_column(Uuid,nullable=True,)
    be_plan_name: Mapped[str | None] = mapped_column(String(128))
    be_plan251_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan252_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan253_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan254_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan255_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan256_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan257_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan258_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    be_plan259_expired: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


    # Canadian Payroll Fields
    be_number: Mapped[str] = mapped_column(String(50), nullable=True)  # CRA Business Number (BN)
    payroll_account_number: Mapped[str] = mapped_column(String(50), nullable=True)  # CRA Payroll Account Number
    province: Mapped[str] = mapped_column(String(20), nullable=True, default="ON")  # Province code (ON for Ontario)
    country: Mapped[str] = mapped_column(String(20), nullable=True, default="CA")  # Country code (CA for Canada)

    # Address Fields
    street_address: Mapped[str] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=True)
    postal_code: Mapped[str] = mapped_column(String(7), nullable=True)  # Canadian postal code format

    # Contact Information
    phone: Mapped[str] = mapped_column(String, nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)

    # Ontario-specific Fields
    wsib_number: Mapped[str] = mapped_column(String, nullable=True)  # Workers' Safety and Insurance Board number
    eht_account: Mapped[str] = mapped_column(String, nullable=True)  # Employer Health Tax account number

    # Payroll Configuration
    remittance_frequency: Mapped[str] = mapped_column(String, nullable=True, default="monthly")  # monthly, quarterly
    tax_year_end: Mapped[Date] = mapped_column(Date, nullable=True)  # Tax year end date

    # Business Information
    legal_name: Mapped[str] = mapped_column(String, nullable=True)  # Legal registered name
    operating_name: Mapped[str] = mapped_column(String, nullable=True)  # Operating/trading name
    business_type: Mapped[str] = mapped_column(String, nullable=True)  # corporation, partnership, sole_prop, etc.
    incorporation_date: Mapped[Date] = mapped_column(Date, nullable=True)
    employee_count: Mapped[int] = mapped_column(nullable=True)  # Approximate number of employees

    # Stripe subscription fields (tenant-owned)
    stripe_customer_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    stripe_subscription_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    stripe_price_id: Mapped[str] = mapped_column(String, nullable=True)
    stripe_status: Mapped[str] = mapped_column(String, nullable=True)
    stripe_current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    stripe_cancel_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    stripe_plan_key: Mapped[str] = mapped_column(String, nullable=True)
    stripe_interval: Mapped[str] = mapped_column(String, nullable=True)
    stripe_latest_event_id: Mapped[str] = mapped_column(String, nullable=True)

    
