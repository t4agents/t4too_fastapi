from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_rls import get_db_rls
from app.db.models.ainvoaic.i_nvoice import InvoiceDB
from app.db.models.ainvoaic.i_nvoice_payment import InvoicePaymentDB
from app.schemas.sch_inv import InvCreate, InvOut, InvPaymentCreate, InvPaymentOut
from app.service.ser_inv import (create_or_update_invoice, create_or_update_invoice_payment,
                                 fetch_invoice_by_id, fetch_invoice_payments, fetch_invoices,)

invMainRou = APIRouter()


def _to_out(inv: InvoiceDB) -> InvOut:
    return InvOut(
        inv_id=inv.id,
        user_id=inv.usr_id,
        be_id=inv.biz_id,
        inv_number=inv.inv_number,
        inv_date=inv.inv_date,
        inv_due_date=inv.inv_due_date,
        inv_title=inv.inv_title,
        inv_template_id=inv.inv_template_id,
        client_id=inv.client_id,
        client_company_name=inv.client_company_name,
        inv_payment_term=inv.inv_payment_term,
        inv_payment_requirement=inv.inv_payment_requirement,
        inv_reference=inv.inv_reference,
        inv_currency=inv.inv_currency,
        inv_subtotal=inv.inv_subtotal,
        inv_discount=inv.inv_discount,
        inv_tax_label=inv.inv_tax_label,
        inv_tax_rate=inv.inv_tax_rate,
        inv_tax_amount=inv.inv_tax_amount,
        inv_shipping=inv.inv_shipping,
        inv_handling=inv.inv_handling,
        inv_deposit=inv.inv_deposit,
        inv_adjustment=inv.inv_adjustment,
        inv_other_charges_label=inv.inv_other_charges_label,
        inv_other_charges_amount=inv.inv_other_charges_amount,
        inv_total=inv.inv_total,
        inv_paid_total=inv.inv_paid_total,
        inv_balance_due=inv.inv_balance_due,
        inv_payment_status=inv.inv_payment_status,
        inv_tnc=inv.inv_tnc or inv.inv_terms_conditions,
        inv_notes=inv.inv_notes,
        inv_items=[],
        inv_payments=[],
        status=inv.status,
        is_active=0 if bool(inv.is_deleted) else 1,
        is_locked=1 if bool(inv.is_flag) else 0,
        is_deleted=1 if bool(inv.is_deleted) else 0,
        created_at=inv.created_at,
        updated_at=inv.created_at,
    )


def _to_payment_out(payment: InvoicePaymentDB) -> InvPaymentOut:
    return InvPaymentOut(
        id=payment.id,
        inv_id=payment.inv_id,
        pm_id=payment.pm_id,
        pm_name=payment.pm_name,
        pm_note=payment.pm_note,
        pay_date=payment.pay_date,
        pay_amount=payment.pay_amount,
        pay_reference=payment.pay_reference,
        pay_note=payment.pay_note,
        status=payment.status,
        is_active=0 if bool(payment.is_deleted) else 1,
        is_locked=1 if bool(payment.is_flag) else 0,
        is_deleted=1 if bool(payment.is_deleted) else 0,
        created_at=payment.created_at,
        updated_at=payment.created_at,
    )


@invMainRou.get("/get_inv_list", response_model=list[InvOut])
async def get_invoices(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    invs = await fetch_invoices(db)
    return [_to_out(inv) for inv in invs]


@invMainRou.get("/get_inv_one", response_model=InvOut)
async def get_invoice_one(
    inv_id: str,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    try:
        inv_uuid = UUID(str(inv_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="inv_id must be a valid UUID") from exc
    inv = await fetch_invoice_by_id(zuid, db, inv_uuid)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _to_out(inv)


@invMainRou.post("/post_inv_one", response_model=InvOut)
async def post_invoice_one(
    payload: InvCreate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    inv = await create_or_update_invoice(zuid, db, payload.model_dump(exclude_unset=True))
    return _to_out(inv)


@invMainRou.get("/get_inv_payment_list", response_model=list[InvPaymentOut])
async def get_invoice_payment_list(
    inv_id: str,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    try:
        inv_uuid = UUID(str(inv_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="inv_id must be a valid UUID") from exc
    payments = await fetch_invoice_payments(zuid, db, inv_uuid)
    return [_to_payment_out(payment) for payment in payments]


@invMainRou.post("/post_inv_payment", response_model=InvPaymentOut)
async def post_invoice_payment(
    payload: InvPaymentCreate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_rls),
):
    try:
        payment = await create_or_update_invoice_payment(
            zuid, db, payload.model_dump(exclude_unset=True)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_payment_out(payment)
