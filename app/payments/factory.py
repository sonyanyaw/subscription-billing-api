from app.db.models.enums import PaymentProvider
from app.payments.mock import MockProvider
from app.payments.stripe_provider import StripeProvider
from app.payments.yookassa import YooKassaProvider

# Which currencies each provider can accept. None = any currency (e.g. mock).
PROVIDER_CURRENCIES: dict[PaymentProvider, set[str] | None] = {
    PaymentProvider.stripe: {"USD", "EUR", "GBP"},
    PaymentProvider.yookassa: {"RUB"},
    PaymentProvider.mock: None,
}


def provider_supports_currency(provider: PaymentProvider, currency: str) -> bool:
    allowed = PROVIDER_CURRENCIES.get(provider)
    return allowed is None or currency.upper() in allowed


def get_provider(provider: PaymentProvider):

    if provider == PaymentProvider.mock:
        return MockProvider()

    if provider == PaymentProvider.stripe:
        return StripeProvider()

    if provider == PaymentProvider.yookassa:
        return YooKassaProvider()

    raise ValueError("Unknown provider")
