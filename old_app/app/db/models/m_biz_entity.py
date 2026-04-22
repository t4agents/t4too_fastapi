from sqlalchemy import String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .m_base import Base, BaseMixin


class BizEntity(Base, BaseMixin):
    __tablename__ = "biz_entities"

    type: Mapped[str] = mapped_column(String, nullable=False, default="FIRM")
    name: Mapped[str] = mapped_column(String, nullable=False, default="my org")

    # Canadian Payroll Fields
    business_number: Mapped[str] = mapped_column(String(15), nullable=True)  # CRA Business Number (BN)
    payroll_account_number: Mapped[str] = mapped_column(String(15), nullable=True)  # CRA Payroll Account Number
    province: Mapped[str] = mapped_column(String(2), nullable=True, default="ON")  # Province code (ON for Ontario)

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