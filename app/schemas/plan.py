from pydantic import BaseModel, ConfigDict
from uuid import UUID


class PlanBase(BaseModel):
    name: str
    price: float
    currency: str
    api_limit: int
    is_active: bool = True


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    currency: str | None = None
    api_limit: int | None = None
    is_active: bool | None = None


class PlanOut(PlanBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)