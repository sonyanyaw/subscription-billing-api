from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class APIUsage(BaseModel):
    id: UUID
    user_id: UUID
    period_start: datetime
    period_end: datetime
    requests_count: int

    model_config = ConfigDict(from_attributes=True)