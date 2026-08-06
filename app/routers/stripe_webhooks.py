# backend/app/routers/stripe_webhooks.py
import os
import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, SubscriptionTier, CreditTransaction

router = APIRouter(prefix="/api/v1/webhooks", tags=["Monetization"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

TIER_CREDIT_MONTHLY_REFILL = {
    SubscriptionTier.STARTER: 500,
    SubscriptionTier.PRO: 3000,
    SubscriptionTier.ENTERPRISE: 10000,
}

@router.post("/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        customer_id = session_obj.get("customer")
        client_reference_id = session_obj.get("client_reference_id")  # User UUID

        # Fetch user & top-up credits
        stmt = select(User).where(User.id == client_reference_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.stripe_customer_id = customer_id
            user.credits_balance += 1000  # On-demand credit purchase
            db.add(CreditTransaction(
                user_id=user.id,
                amount=1000,
                description="Stripe Checkout Credit Top-up"
            ))
            await db.commit()

    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        customer_id = sub["customer"]
        
        stmt = select(User).where(User.stripe_customer_id == customer_id)
        user = (await db.execute(stmt)).scalar_one_or_none()
        if user:
            # Plan upgrades
            user.tier = SubscriptionTier.PRO
            user.credits_balance += TIER_CREDIT_MONTHLY_REFILL[SubscriptionTier.PRO]
            await db.commit()

    return {"status": "success"}
