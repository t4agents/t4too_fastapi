from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_zuid
from app.db.conn.db_async import get_db_admin
from app.db.models.too.z_client import ZClientDB
from app.schemas.sch_client import ClientCreate, ClientOut
from app.service.ser_client import create_or_update_client, fetch_clients

clientRou = APIRouter()


def _to_out(client: ZClientDB) -> ClientOut:
    return ClientOut(
        id=client.id,
        client_number=client.client_number,
        client_business_number=client.client_business_number,
        client_company_name=client.client_company_name,
        client_contact_name=client.client_contact_name,
        client_contact_title=client.client_contact_title,
        client_address=client.client_address,
        client_email=client.client_email,
        client_mainphone=client.client_mainphone,
        client_secondphone=client.client_secondphone,
        client_fax=client.client_fax,
        client_website=client.client_website,
        client_currency=client.client_currency,
        client_tax_id=client.client_tax_id,
        client_payment_term=client.client_payment_term,
        client_payment_method=client.client_payment_method,
        client_template_id=client.client_template_id,
        client_terms_conditions=client.client_terms_conditions,
        client_note=client.client_note,
        client_status=client.client_status,
    )


@clientRou.get("/get_client_list", response_model=list[ClientOut])
async def get_clients(
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    clients = await fetch_clients(zuid, db)
    return [_to_out(client) for client in clients]


@clientRou.post("/post_client", response_model=ClientOut)
async def post_client(
    payload: ClientCreate,
    zuid: UUID = Depends(get_zuid),
    db: AsyncSession = Depends(get_db_admin),
):
    client = await create_or_update_client(zuid, db, payload.model_dump(exclude_unset=True))
    return _to_out(client)
