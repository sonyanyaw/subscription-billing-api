import logging

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db
from app.services.payment_service import PaymentService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )

    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    
    logger.info("Stripe webhook received: %s", event_type)

    if event_type == "payment_intent.succeeded":
        intent = event["data"]["object"]
        await PaymentService.handle_stripe_success(db, intent["id"])

    elif event_type == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        await PaymentService.handle_stripe_failed(db, payment_intent["id"])

    else:
        pass

    return {"status": "ok"}