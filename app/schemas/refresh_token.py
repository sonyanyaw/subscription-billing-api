from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class RefreshToken(BaseModel):
    id: UUID
    user_id: UUID
    expires_at: datetime
    revoked: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)