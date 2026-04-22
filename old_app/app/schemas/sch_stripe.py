from typing import Literal, Optional

from pydantic import BaseModel, Field


class StripeCheckoutRequest(BaseModel):
    plan_key: Literal["basic", "pro", "enterprise"] = Field(..., description="Plan key")
    interval: Literal["month", "year"] = Field(..., description="Billing interval")


class StripeCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class StripePortalResponse(BaseModel):
    portal_url: str


class StripeWebhookResponse(BaseModel):
    received: bool = True
    event_id: Optional[str] = None
