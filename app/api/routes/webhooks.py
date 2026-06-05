import logging

import stripe
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_db
from app.db.models.enums import WebhookEventStatus
from app.services.payment_service import PaymentService
from app.services.webhook_event_service import WebhookEventService

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
    provider_payment_id = event["data"]["object"]["id"]

    logger.info("Stripe webhook received: %s  payment_id=%s", event_type, provider_payment_id)

    db_event = await WebhookEventService.log(
        db,
        event_type=event_type,
        provider_payment_id=provider_payment_id,
        status=WebhookEventStatus.received,
        payload=event.to_dict_recursive(),
    )

    try:
        if event_type == "payment_intent.succeeded":
            await PaymentService.handle_stripe_success(db, provider_payment_id)
            db_event.status = WebhookEventStatus.processed

        elif event_type == "payment_intent.payment_failed":
            await PaymentService.handle_stripe_failed(db, provider_payment_id)
            db_event.status = WebhookEventStatus.processed

        else:
            logger.info("Unhandled Stripe event type: %s", event_type)
            db_event.status = WebhookEventStatus.processed

        await db.commit()

    except Exception as e:
        logger.exception("Error processing webhook %s: %s", event_type, e)
        db_event.status = WebhookEventStatus.failed
        await db.commit()

    return {"status": "ok"}