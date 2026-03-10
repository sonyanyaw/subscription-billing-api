from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.schemas.user import UserOut
from app.db.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user