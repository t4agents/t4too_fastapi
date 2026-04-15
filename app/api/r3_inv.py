from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.ainvoaic.i_nvoice import InvoiceDB
from app.schemas.sch_inv import InvOut
from app.service.ser_inv import fetch_invoices

invRou = APIRouter()


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


@invRou.get("/r3_inv_list", response_model=list[InvOut])
async def get_invoices(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    invs = await fetch_invoices(zuid, db)
    return [_to_out(inv) for inv in invs]

