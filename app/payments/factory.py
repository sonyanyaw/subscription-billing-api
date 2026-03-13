from app.db.models.enums import PaymentProvider
from app.payments.mock import MockProvider
from app.payments.stripe import StripeProvider
# from app.payments.yookassa import YooKassaProvider


def get_provider(provider: PaymentProvider):

    if provider == PaymentProvider.mock:
        return MockProvider()

    if provider == PaymentProvider.stripe:
        return StripeProvider()

    # if provider == PaymentProvider.yookassa:
    #     return YooKassaProvider()

    raise ValueError("Unknown provider")