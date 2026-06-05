import uuid
from datetime import datetime
from sqlalchemy import DateTime, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base
from app.db.models.enums import WebhookEventStatus


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[WebhookEventStatus] = mapped_column(
        Enum(WebhookEventStatus), default=WebhookEventStatus.received
    )
    payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
