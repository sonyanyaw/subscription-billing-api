import uuid
from sqlalchemy import String, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.models.base import Base


class PlanPrice(Base):
    __tablename__ = "plan_prices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    plan = relationship("Plan", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("plan_id", "currency", name="uq_plan_prices_plan_id_currency"),
    )
