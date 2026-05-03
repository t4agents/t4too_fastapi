from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Sequence

from sqlalchemy import Date, Numeric, String, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.too.z_base import Base
from app.db.schemas.schemas import SCHEMA_TOO_ACC


class VendorMCPDB(Base):
    __tablename__ = "mcp_vendors"
    __table_args__ = {"schema": SCHEMA_TOO_ACC}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)


class BankTransactionMCPDB(Base):
    __tablename__ = "mcp_bank_transactions"
    __table_args__ = {"schema": SCHEMA_TOO_ACC}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    posted_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)


async def get_vendor_by_name(db: AsyncSession, name: str) -> VendorMCPDB | None:
    normalized = name.strip().lower()
    stmt = select(VendorMCPDB).where(func.lower(VendorMCPDB.name) == normalized)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_recent_bank_transactions(
    db: AsyncSession,
    account_name: str,
    limit: int = 5,
) -> Sequence[BankTransactionMCPDB]:
    key = account_name.strip().lower()
    stmt = (
        select(BankTransactionMCPDB)
        .where(func.lower(BankTransactionMCPDB.account_name) == key)
        .order_by(desc(BankTransactionMCPDB.posted_at))
        .limit(max(1, limit))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
