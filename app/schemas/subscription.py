from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from app.schemas.plan import PlanOut
from app.db.models.enums import SubscriptionStatus
from app.schemas.user import UserOut

class SubscriptionBase(BaseModel):
    status: SubscriptionStatus
    cancel_at_period_end: bool = False

class SubscriptionCreate(BaseModel):
    user_id: UUID
    plan_id: UUID

class SubscriptionUpdate(BaseModel):
    status: SubscriptionStatus | None = None
    cancel_at_period_end: bool | None = None

class SubscriptionOut(SubscriptionBase):
    id: UUID
    user_id: UUID
    plan: PlanOut
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionWithUserOut(SubscriptionBase):
    id: UUID
    user: UserOut
    plan: PlanOut
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)