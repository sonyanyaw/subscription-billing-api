from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.db.models.plan import Plan
from app.schemas.plan import PlanOut


router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(Plan))

    return result.scalars().all()
