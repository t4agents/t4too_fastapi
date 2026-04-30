from typing import TypedDict


class CoaTemplateAccount(TypedDict):
    code: str
    name: str
    type: str


def generic_startup_template() -> list[CoaTemplateAccount]:
    # Optional fallback template for teams-of-one who do not provide a custom COA yet.
    return [
        {"code": "1000", "name": "Cash", "type": "asset"},
        {"code": "1100", "name": "Accounts Receivable", "type": "asset"},
        {"code": "1500", "name": "Computer Equipment", "type": "asset"},
        {"code": "2000", "name": "Accounts Payable", "type": "liability"},
        {"code": "2100", "name": "GST/HST Payable", "type": "liability"},
        {"code": "3000", "name": "Owner Equity", "type": "equity"},
        {"code": "3100", "name": "Retained Earnings", "type": "equity"},
        {"code": "4000", "name": "Service Revenue", "type": "revenue"},
        {"code": "5000", "name": "Software Subscriptions", "type": "expense"},
        {"code": "5100", "name": "Contractors", "type": "expense"},
        {"code": "5200", "name": "Office Expense", "type": "expense"},
        {"code": "5300", "name": "Meals and Entertainment", "type": "expense"},
        {"code": "5400", "name": "Bank Fees", "type": "expense"},
    ]

