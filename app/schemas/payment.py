from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

from app.db.models.enums import PaymentProvider, PaymentStatus


class PaymentBase(BaseModel):
    invoice_id: UUID
    provider: PaymentProvider

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    status: PaymentStatus | None = None

class PaymentOut(PaymentBase):
    id: UUID
    provider_payment_id: str
    provider: PaymentProvider
    status: PaymentStatus
    created_at: datetime
    confirmation_url: str | None = None

    model_config = ConfigDict(from_attributes=True)