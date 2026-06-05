from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.db.models.api_usage import APIUsage

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/")
async def get_usage(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    result = await db.execute(
        select(APIUsage).where(
            APIUsage.user_id == current_user.id
        )
    )

    return result.scalars().all()