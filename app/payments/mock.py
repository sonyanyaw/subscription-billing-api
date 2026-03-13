import uuid


class MockProvider:

    async def create_payment(self, invoice):

        return {
            "provider_payment_id": f"mock_{uuid.uuid4()}",
            "confirmation_url": None
        }
