import asyncio
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeProvider:

    async def create_payment(self, invoice):

        intent = await asyncio.to_thread(
            stripe.PaymentIntent.create,
            amount=int(invoice.amount * 100),
            currency=invoice.currency.lower(),
            description=f"Subscription invoice {invoice.id}",
            expand=["latest_charge"],
            metadata={"invoice_id": str(invoice.id)},
            automatic_payment_methods={
                "enabled": True,
                "allow_redirects": "never"
            },
            idempotency_key=f"invoice-{invoice.id}"
        )

        return {
            "provider_payment_id": intent.id,
            "confirmation_url": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status
        }