from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class InvOut(BaseModel):
    inv_id: UUID
    user_id: UUID | None = None
    be_id: UUID | None = None

    inv_number: str | None = None
    inv_date: datetime | None = None
    inv_due_date: datetime | None = None
    inv_title: str | None = None
    inv_template_id: str | None = None

    client_id: UUID | None = None
    client_company_name: str | None = None

    inv_payment_term: int | None = None
    inv_payment_requirement: str | None = None
    inv_reference: str | None = None
    inv_currency: str | None = None

    inv_subtotal: float | None = None
    inv_discount: float | None = None
    inv_tax_label: str | None = None
    inv_tax_rate: float | None = None
    inv_tax_amount: float | None = None
    inv_shipping: float | None = None
    inv_handling: float | None = None
    inv_deposit: float | None = None
    inv_adjustment: float | None = None
    inv_other_charges_label: str | None = None
    inv_other_charges_amount: float | None = None
    inv_total: float | None = None

    inv_paid_total: float | None = None
    inv_balance_due: float | None = None
    inv_payment_status: str | None = None

    inv_tnc: str | None = None
    inv_notes: str | None = None
    inv_items: list[dict[str, Any]] = Field(default_factory=list)
    inv_payments: list[dict[str, Any]] = Field(default_factory=list)

    status: str | None = None
    is_active: int = 1
    is_locked: int = 0
    is_deleted: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None
