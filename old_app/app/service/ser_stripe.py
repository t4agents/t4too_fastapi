from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import stripe
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings_singleton
from app.db.models import m_be, m_user
from app.schemas.sch_stripe import StripeCheckoutRequest


settings = get_settings_singleton()
stripe.api_key = settings.STRIPE_SECRET_KEY


def _price_map() -> Dict[str, Dict[str, str]]:
    return {
        "basic": {
            "month": settings.STRIPE_PRICE_BASIC_MONTH,
            "year": settings.STRIPE_PRICE_BASIC_YEAR,
        },
        "pro": {
            "month": settings.STRIPE_PRICE_PRO_MONTH,
            "year": settings.STRIPE_PRICE_PRO_YEAR,
        },
        "enterprise": {
            "month": settings.STRIPE_PRICE_ENTERPRISE_MONTH,
            "year": settings.STRIPE_PRICE_ENTERPRISE_YEAR,
        },
    }


def _get_price_id(plan_key: str, interval: str) -> str:
    price_id = _price_map().get(plan_key, {}).get(interval, "")
    if not price_id:
        raise HTTPException(status_code=500, detail="Stripe price ID not configured")
    return price_id


async def _get_tenant_be(tenant_id, db: AsyncSession) -> m_be.BizEntity:
    result = await db.execute(select(m_be.BizEntity).where(m_be.BizEntity.id == tenant_id))
    be = result.scalar_one_or_none()
    if not be:
        raise HTTPException(status_code=404, detail="Tenant business entity not found")
    return be


async def _get_user_email(user_id, db: AsyncSession) -> str | None:
    result = await db.execute(select(m_user.UserDB).where(m_user.UserDB.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return None
    return user.email


async def create_checkout_session(
    payload: StripeCheckoutRequest,
    tenant_id,
    user_id,
    db: AsyncSession,
) -> stripe.checkout.Session:
    be = await _get_tenant_be(tenant_id, db)
    email = await _get_user_email(user_id, db)

    price_id = _get_price_id(payload.plan_key, payload.interval)

    if not be.stripe_customer_id:
        customer = stripe.Customer.create(
            email=email,
            metadata={
                "tenant_id": str(tenant_id),
                "user_id": str(user_id),
            },
        )
        be.stripe_customer_id = customer.id

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=be.stripe_customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=settings.STRIPE_SUCCESS_URL,
        cancel_url=settings.STRIPE_CANCEL_URL,
        subscription_data={
            "metadata": {
                "tenant_id": str(tenant_id),
                "plan_key": payload.plan_key,
                "interval": payload.interval,
            }
        },
    )

    be.stripe_price_id = price_id
    be.stripe_plan_key = payload.plan_key
    be.stripe_interval = payload.interval

    await db.commit()
    return session


async def create_portal_session(tenant_id, db: AsyncSession) -> stripe.billing_portal.Session:
    be = await _get_tenant_be(tenant_id, db)
    if not be.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Stripe customer not found for tenant")

    portal = stripe.billing_portal.Session.create(
        customer=be.stripe_customer_id,
        return_url=settings.STRIPE_PORTAL_RETURN_URL or settings.STRIPE_SUCCESS_URL,
    )
    return portal


def _from_unix_ts(ts: int | None) -> datetime | None:
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


async def _apply_subscription_update(
    db: AsyncSession,
    customer_id: str,
    subscription: stripe.Subscription,
    event_id: str | None,
) -> None:
    result = await db.execute(select(m_be.BizEntity).where(m_be.BizEntity.stripe_customer_id == customer_id))
    be = result.scalar_one_or_none()
    if not be:
        raise HTTPException(status_code=404, detail="Tenant business entity not found for customer")

    price_id = None
    if subscription.get("items") and subscription["items"]["data"]:
        price_id = subscription["items"]["data"][0]["price"]["id"]

    be.stripe_subscription_id = subscription.get("id")
    be.stripe_status = subscription.get("status")
    be.stripe_price_id = price_id or be.stripe_price_id
    be.stripe_current_period_end = _from_unix_ts(subscription.get("current_period_end"))
    be.stripe_cancel_at_period_end = subscription.get("cancel_at_period_end")
    be.stripe_cancel_at = _from_unix_ts(subscription.get("cancel_at"))
    be.stripe_latest_event_id = event_id

    await db.commit()


async def handle_webhook_event(payload: bytes, sig_header: str | None, db: AsyncSession) -> str:
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook secret not configured")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {exc}") from exc

    event_type = event.get("type")
    event_id = event.get("id")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        if session.get("mode") == "subscription":
            subscription_id = session.get("subscription")
            customer_id = session.get("customer")
            if subscription_id and customer_id:
                subscription = stripe.Subscription.retrieve(subscription_id)
                await _apply_subscription_update(db, customer_id, subscription, event_id)

    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted"):
        subscription = event["data"]["object"]
        customer_id = subscription.get("customer")
        if customer_id:
            await _apply_subscription_update(db, customer_id, subscription, event_id)

    return event_id or ""
