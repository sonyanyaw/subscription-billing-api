import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Enum, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base
from app.db.models.enums import InvoiceStatus


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        index=True
    )

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str]

    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus),
        default=InvoiceStatus.draft
    )

    due_date: Mapped[datetime]
    paid_at: Mapped[datetime | None]

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    subscription = relationship("Subscription", back_populates="invoices")
    payment = relationship("Payment", back_populates="invoice", uselist=False)