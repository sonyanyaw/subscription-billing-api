import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base
from app.db.models.enums import PaymentStatus, PaymentProvider


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    invoice_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"),
        unique=True
    )

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider)
    )

    provider_payment_id: Mapped[str] = mapped_column(String(255))

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.pending
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="payment")