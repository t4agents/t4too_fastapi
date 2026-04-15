from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

SEED_VERSION = "v1"


@dataclass(frozen=True)
class SeedBizDefaults:
    be_name: str
    be_type: str
    be_currency: str
    be_payment_term: int
    be_inv_prefix: str
    be_inv_integer: int
    be_inv_integer_max: int
    be_date_format: str
    be_timezone: str


BIZ_DEFAULTS = SeedBizDefaults(
    be_name="My Business",
    be_type="ME",
    be_currency="USD",
    be_payment_term=7,
    be_inv_prefix="INV-",
    be_inv_integer=2501,
    be_inv_integer_max=2501,
    be_date_format="MM/DD/YYYY",
    be_timezone="America/Toronto",
)


CLIENT_TEMPLATES: list[dict[str, Any]] = [
    {
        "seed_key": "client_demo_1",
        "client_number": "c_demo_1",
        "client_company_name": "Sterling Group (Demo)",
        "client_contact_name": "Rebecca Hughes",
        "client_contact_title": "Manager",
        "client_business_number": "123456RT001",
        "client_tax_id": "123456RT001",
        "client_address": "101 Market Street, San Francisco, CA 94105",
        "client_email": "rebecca.hughes@sterling.ai",
        "client_mainphone": "555-123-4567",
        "client_website": "https://sterling.ai",
        "client_currency": "USD",
        "client_template_id": "t1",
        "client_status": "active",
        "client_note": "Demo client seeded by system.",
        "client_payment_method": "Bank Transfer",
        "client_payment_term": 15,
        "client_terms_conditions": "Payment due in 15 days.",
    },
    {
        "seed_key": "client_demo_2",
        "client_number": "c_demo_2",
        "client_company_name": "Summit Tech Partners (Demo)",
        "client_contact_name": "Jason Liu",
        "client_contact_title": "Director",
        "client_business_number": "868-581-001",
        "client_tax_id": "868-581-001",
        "client_address": "202 Innovation Way, Austin, TX 78701",
        "client_email": "jason.liu@summittech.com",
        "client_mainphone": "555-987-6543",
        "client_website": "https://summittech.com",
        "client_currency": "USD",
        "client_template_id": "t1",
        "client_status": "active",
        "client_note": "Demo client seeded by system.",
        "client_payment_method": "Bank Transfer",
        "client_payment_term": 30,
        "client_terms_conditions": "Payment due in 30 days.",
    },
]


ITEM_TEMPLATES: list[dict[str, Any]] = [
    {
        "seed_key": "item_adjustment",
        "item_number": "P002",
        "item_name": "Adjustment",
        "item_rate": 1.00,
        "item_unit": "item",
        "item_sku": "SKU-4225-776-3234",
        "item_description": "Additional charges or credits.",
    },
    {
        "seed_key": "item_product",
        "item_number": "P003",
        "item_name": "Product",
        "item_rate": 1500.00,
        "item_unit": "project",
        "item_sku": "6IN-RD-CM-CO",
        "item_description": "Tangible goods or materials delivered.",
    },
    {
        "seed_key": "item_consulting",
        "item_number": "P0031",
        "item_name": "Consulting Session",
        "item_rate": 100.00,
        "item_unit": "hour",
        "item_sku": "SH123-BLK-8",
        "item_description": "Business strategy session (1 hour).",
    },
]


PAYMENT_METHOD_TEMPLATES: list[dict[str, Any]] = [
    {"seed_key": "pm_deposit", "pm_name": "Deposit", "pm_note": "Deposit."},
    {
        "seed_key": "pm_credit_card",
        "pm_name": "Credit Card",
        "pm_note": "Processed via Stripe, Square, PayPal, or similar processors.",
    },
    {
        "seed_key": "pm_bank_transfer",
        "pm_name": "Bank Transfer",
        "pm_note": "ACH or EFT transfer from bank account.",
    },
    {"seed_key": "pm_check", "pm_name": "Check", "pm_note": "Payable to your business name."},
    {"seed_key": "pm_cash", "pm_name": "Cash", "pm_note": "For in-person transactions only."},
    {"seed_key": "pm_other", "pm_name": "Other", "pm_note": "Refer to invoice notes."},
]


FEE_TEMPLATES: list[dict[str, Any]] = [
    {
        "seed_key": "fee_shipping",
        "fee_name": "Shipping",
        "fee_amount": 10.00,
        "fee_note": "Shipping charges.",
    },
    {
        "seed_key": "fee_handling",
        "fee_name": "Handling",
        "fee_amount": 100.00,
        "fee_note": "Packaging, handling, or special processing.",
    },
    {
        "seed_key": "fee_late_fee",
        "fee_name": "Late Fee",
        "fee_amount": 1.00,
        "fee_note": "Fee applied for overdue invoices.",
    },
]


TAX_TEMPLATES: list[dict[str, Any]] = [
    {
        "seed_key": "tax_hst",
        "tax_name": "HST",
        "tax_rate": 13.0,
        "tax_type": "federal",
        "tax_note": "Canada Harmonized Sales Tax",
    },
    {
        "seed_key": "tax_gst",
        "tax_name": "GST",
        "tax_rate": 5.0,
        "tax_type": "federal",
        "tax_note": "Canada Goods and Services Tax",
    },
    {
        "seed_key": "tax_pst",
        "tax_name": "PST",
        "tax_rate": 7.0,
        "tax_type": "provincial",
        "tax_note": "Provincial Sales Tax (for example BC).",
    },
    {
        "seed_key": "tax_sales_us",
        "tax_name": "Sales Tax",
        "tax_rate": 8.875,
        "tax_type": "state",
        "tax_note": "US sample sales tax.",
    },
]


INVOICE_TEMPLATES: list[dict[str, Any]] = [
    {
        "seed_key": "inv_demo_1",
        "inv_number": "INV-1001",
        "inv_title": "Invoice for Demo Client 1",
        "inv_reference": "PO#-001",
        "inv_currency": "USD",
        "inv_payment_requirement": "Net 7 days",
        "inv_payment_term": 7,
        "inv_date": datetime.now(timezone.utc),
        "inv_due_date": datetime.now(timezone.utc),
        "inv_subtotal": 240.00,
        "inv_discount": 0.00,
        "inv_tax_label": "Tax",
        "inv_tax_rate": 0.00,
        "inv_tax_amount": 0.00,
        "inv_shipping": 0.00,
        "inv_handling": 0.00,
        "inv_deposit": 0.00,
        "inv_adjustment": 0.00,
        "inv_other_charges_label": "Other Charges",
        "inv_other_charges_amount": 0.00,
        "inv_total": 240.00,
        "inv_paid_total": 0.00,
        "inv_balance_due": 240.00,
        "inv_payment_status": "Unpaid",
        "inv_flag_word": "Unpaid",
        "inv_flag_emoji": "pending",
        "inv_pdf_template": "default",
        "inv_notes": "Thank you for your business!",
        "inv_terms_conditions": "Thank you for your business!",
        "client_seed_key": "client_demo_1",
        "items": [
            {
                "item_seed_key": "item_consulting",
                "item_quantity": 2,
                "item_rate": 120.00,
                "item_amount": 240.00,
                "item_note": "notes",
            }
        ],
        "payments": [],
    },
    {
        "seed_key": "inv_demo_2",
        "inv_number": "INV-1002",
        "inv_title": "Invoice for Demo Client 2",
        "inv_reference": "PO#-002",
        "inv_currency": "USD",
        "inv_payment_requirement": "Net 10 days",
        "inv_payment_term": 10,
        "inv_date": datetime.now(timezone.utc),
        "inv_due_date": datetime.now(timezone.utc),
        "inv_subtotal": 1500.00,
        "inv_discount": 0.00,
        "inv_tax_label": "Tax",
        "inv_tax_rate": 0.13,
        "inv_tax_amount": 195.00,
        "inv_shipping": 0.00,
        "inv_handling": 0.00,
        "inv_deposit": 0.00,
        "inv_adjustment": 0.00,
        "inv_other_charges_label": "Other Charges",
        "inv_other_charges_amount": 0.00,
        "inv_total": 1695.00,
        "inv_paid_total": 1695.00,
        "inv_balance_due": 0.00,
        "inv_payment_status": "Paid",
        "inv_flag_word": "Paid",
        "inv_flag_emoji": "paid",
        "inv_pdf_template": "default",
        "inv_notes": "Thank you for your business!",
        "inv_terms_conditions": "Thank you for your business!",
        "client_seed_key": "client_demo_2",
        "items": [
            {
                "item_seed_key": "item_product",
                "item_quantity": 1,
                "item_rate": 1500.00,
                "item_amount": 1500.00,
                "item_note": "notes",
            }
        ],
        "payments": [
            {
                "payment_seed_key": "inv_demo_2_pay_1",
                "payment_method_seed_key": "pm_bank_transfer",
                "pay_amount": 1695.00,
                "pay_reference": "TRX001",
                "pay_note": "Paid in full",
                "pay_date": datetime.now(timezone.utc),
            }
        ],
    },
]
