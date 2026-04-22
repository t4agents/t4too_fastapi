from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.dependency_injection import ZMeDataClass, get_zme
from app.db.db_async import get_db_admin
from app.schemas.sch_stripe import (
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripePortalResponse,
    StripeWebhookResponse,
)
from app.service.ser_stripe import create_checkout_session, create_portal_session, handle_webhook_event

stripeRou = APIRouter()


@stripeRou.post("/checkout-session", response_model=StripeCheckoutResponse)
async def checkout_session(
    payload: StripeCheckoutRequest,
    zme: ZMeDataClass = Depends(get_zme),
):
    session = await create_checkout_session(payload, zme.ztid, zme.zuid, zme.zdb)
    if not session.url:
        raise HTTPException(status_code=500, detail="Stripe checkout session URL missing")
    return StripeCheckoutResponse(checkout_url=session.url, session_id=session.id)


@stripeRou.post("/portal-session", response_model=StripePortalResponse)
async def portal_session(
    zme: ZMeDataClass = Depends(get_zme),
):
    portal = await create_portal_session(zme.ztid, zme.zdb)
    return StripePortalResponse(portal_url=portal.url)


@stripeRou.post("/webhook", response_model=StripeWebhookResponse)
async def webhook(
    request: Request,
    db=Depends(get_db_admin),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    event_id = await handle_webhook_event(payload, sig_header, db)
    return StripeWebhookResponse(received=True, event_id=event_id or None)
