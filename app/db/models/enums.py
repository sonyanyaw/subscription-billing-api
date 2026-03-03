import enum


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    canceled = "canceled"
    expired = "expired"
    past_due = "past_due"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    paid = "paid"
    failed = "failed"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    succeeded = "succeeded"
    failed = "failed"


class PaymentProvider(str, enum.Enum):
    stripe = "stripe"
    mock = "mock"