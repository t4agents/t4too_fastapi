from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ClientOut(BaseModel):
    id: UUID
    client_number: Optional[str] = None
    client_business_number: Optional[str] = None
    client_company_name: Optional[str] = None
    client_contact_name: Optional[str] = None
    client_contact_title: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    client_mainphone: Optional[str] = None
    client_secondphone: Optional[str] = None
    client_fax: Optional[str] = None
    client_website: Optional[str] = None
    client_currency: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_payment_term: Optional[int] = None
    client_payment_method: Optional[str] = None
    client_template_id: Optional[str] = None
    client_terms_conditions: Optional[str] = None
    client_note: Optional[str] = None
    client_status: Optional[str] = None


class ClientCreate(BaseModel):
    id: Optional[UUID] = None
    client_number: Optional[str] = None
    client_business_number: Optional[str] = None
    client_company_name: Optional[str] = None
    client_contact_name: Optional[str] = None
    client_contact_title: Optional[str] = None
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    client_mainphone: Optional[str] = None
    client_secondphone: Optional[str] = None
    client_fax: Optional[str] = None
    client_website: Optional[str] = None
    client_currency: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_payment_term: Optional[int] = None
    client_payment_method: Optional[str] = None
    client_template_id: Optional[str] = None
    client_terms_conditions: Optional[str] = None
    client_note: Optional[str] = None
    client_status: Optional[str] = None
