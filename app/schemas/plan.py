from pydantic import BaseModel, ConfigDict
from uuid import UUID


class PlanPriceBase(BaseModel):
    currency: str
    amount: float


class PlanPriceCreate(PlanPriceBase):
    pass


class PlanPriceOut(PlanPriceBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlanBase(BaseModel):
    name: str
    api_limit: int
    is_active: bool = True


class PlanCreate(PlanBase):
    prices: list[PlanPriceCreate]


class PlanUpdate(BaseModel):
    name: str | None = None
    api_limit: int | None = None
    is_active: bool | None = None


class PlanSummary(PlanBase):
    """Lightweight plan view without prices, used nested in other responses."""
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class PlanOut(PlanBase):
    id: UUID
    prices: list[PlanPriceOut]

    model_config = ConfigDict(from_attributes=True)
