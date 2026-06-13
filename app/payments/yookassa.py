import asyncio
import uuid

from yookassa import Configuration, Payment as YooKassaPayment

from app.core.config import settings
from app.payments.base import PaymentProviderBase


class YooKassaProvider(PaymentProviderBase):

    def __init__(self):
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    async def create_payment(self, invoice) -> dict:
        # Deterministic idempotency key - same invoice always maps to the same key,
        # so retrying create_payment for the same invoice won't create duplicate charges.
        idempotency_key = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"invoice-{invoice.id}-{invoice.currency}"))

        payment = await asyncio.to_thread(
            YooKassaPayment.create,
            {
                "amount": {
                    "value": f"{invoice.amount:.2f}",
                    "currency": invoice.currency.upper(),
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": settings.PAYMENT_RETURN_URL,
                },
                "capture": True,
                "description": f"Invoice {invoice.id}",
                "metadata": {"invoice_id": str(invoice.id)},
            },
            idempotency_key,
        )

        return {
            "provider_payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
        }
