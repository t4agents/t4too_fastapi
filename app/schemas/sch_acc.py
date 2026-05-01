from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


AccountType = Literal["asset", "liability", "equity", "revenue", "expense"]
LineType = Literal["debit", "credit"]


class AccountCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=255)
    type: AccountType
    subtype: str | None = None


class AccountOut(BaseModel):
    id: UUID
    code: str
    name: str
    type: AccountType
    subtype: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class TransactionOut(BaseModel):
    id: UUID
    txn_date: date
    description: str
    amount: Decimal
    currency: str
    status: str
    source_file_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JournalGenerateIn(BaseModel):
    transaction_id: UUID


class JournalLineOut(BaseModel):
    id: UUID
    journal_entry_id: UUID
    account_id: UUID
    line_type: LineType
    amount: Decimal
    description: str | None

    model_config = {"from_attributes": True}


class JournalEntryOut(BaseModel):
    id: UUID
    entry_no: int
    entry_date: date
    memo: str | None
    source: str
    period_yyyymm: int
    posted_at: datetime
    is_reversal: bool
    lines: list[JournalLineOut] = []


class TrialBalanceRow(BaseModel):
    account_id: UUID
    code: str
    name: str
    type: AccountType
    debit: Decimal
    credit: Decimal
    net: Decimal


class ReportSectionRow(BaseModel):
    account_id: UUID
    code: str
    name: str
    amount: Decimal


class BalanceSheetOut(BaseModel):
    as_of: date
    assets: list[ReportSectionRow]
    liabilities: list[ReportSectionRow]
    equity: list[ReportSectionRow]
    totals: dict[str, Decimal]


class IncomeStatementOut(BaseModel):
    from_date: date
    to_date: date
    revenue: list[ReportSectionRow]
    expenses: list[ReportSectionRow]
    totals: dict[str, Decimal]

