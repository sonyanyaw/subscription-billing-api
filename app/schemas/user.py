from typing import Annotated
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from app.db.models.enums import UserRole


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: Annotated[str | None, Field(min_length=8)] = None