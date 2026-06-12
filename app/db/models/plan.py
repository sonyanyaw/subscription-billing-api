import uuid
from datetime import datetime
from sqlalchemy import String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.utils import utcnow
from app.db.models.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    api_limit: Mapped[int] = mapped_column(Integer, nullable=False)

    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    subscriptions = relationship("Subscription", back_populates="plan")
    prices = relationship(
        "PlanPrice",
        back_populates="plan",
        cascade="all, delete-orphan",
    )