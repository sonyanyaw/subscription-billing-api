from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.db.models.enums import InvoiceStatus

class InvoiceBase(BaseModel):
    amount: float
    currency: str
    status: InvoiceStatus

class InvoiceCreate(BaseModel):
    subscription_id: UUID
    due_date: datetime
    amount: float
    currency: str

class InvoiceUpdate(BaseModel):
    status: InvoiceStatus | None = None
    paid_at: datetime | None = None

class InvoiceOut(InvoiceBase):
    id: UUID
    user_id: UUID
    subscription_id: UUID
    amount: float
    currency: str
    status: str
    due_date: datetime
    paid_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)