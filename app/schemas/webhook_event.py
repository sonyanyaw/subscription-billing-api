from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.db.models.enums import WebhookEventStatus


class WebhookEventOut(BaseModel):
    id: UUID
    event_type: str
    provider_payment_id: str | None
    status: WebhookEventStatus
    payload: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
