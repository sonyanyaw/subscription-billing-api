from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_admin
from app.db.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate

router = APIRouter(prefix="/admin/plans", tags=["admin/plans"])


@router.get("/", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(Plan))
    return result.scalars().all()


@router.post("/", response_model=PlanOut)
async def create_plan(data: PlanCreate, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    plan = Plan(**data.dict())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: UUID, 
    data: PlanUpdate, 
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin)
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/{plan_id}")
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.delete(plan)
    await db.commit()
    return {"status": "deleted"}