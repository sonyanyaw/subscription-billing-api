from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.schemas.plan import PlanSummary
from app.db.models.enums import SubscriptionStatus
from app.schemas.user import UserOut

class SubscriptionBase(BaseModel):
    status: SubscriptionStatus
    cancel_at_period_end: bool = False

class SubscriptionCreate(BaseModel):
    plan_id: UUID
    currency: str = "USD"

class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus | None = None
    cancel_at_period_end: bool | None = None

class SubscriptionOut(SubscriptionBase):
    id: UUID
    user_id: UUID
    plan: PlanSummary
    currency: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionWithUserOut(SubscriptionBase):
    id: UUID
    user: UserOut
    plan: PlanSummary
    currency: str
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)