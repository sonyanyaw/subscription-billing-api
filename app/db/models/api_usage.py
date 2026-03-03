import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import Base


class APIUsage(Base):
    __tablename__ = "api_usage"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )

    period_start: Mapped[datetime]
    period_end: Mapped[datetime]
    requests_count: Mapped[int] = mapped_column(default=0)