import enum

class AccountType(str, enum.Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"


class SourceType(str, enum.Enum):
    INVOICE = "invoice"
    PAYROLL = "payroll"
    MANUAL = "manual"