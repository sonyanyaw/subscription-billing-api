from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from app.api.deps import get_db, require_admin
from app.db.models.plan import Plan
from app.db.models.plan_price import PlanPrice
from app.schemas.plan import PlanCreate, PlanOut, PlanUpdate

router = APIRouter(prefix="/admin/plans", tags=["admin/plans"])


async def _get_plan_with_prices(db: AsyncSession, plan_id) -> Plan | None:
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id).options(selectinload(Plan.prices))
    )
    return result.scalar_one_or_none()


@router.get("/", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    result = await db.execute(select(Plan).options(selectinload(Plan.prices)))
    return result.scalars().all()


@router.post("/", response_model=PlanOut)
async def create_plan(data: PlanCreate, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    plan = Plan(
        name=data.name,
        api_limit=data.api_limit,
        is_active=data.is_active,
        prices=[PlanPrice(currency=p.currency.upper(), amount=p.amount) for p in data.prices],
    )
    db.add(plan)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Plan name already exists")
    return await _get_plan_with_prices(db, plan.id)


@router.put("/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: UUID,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    plan = await _get_plan_with_prices(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    payload = data.model_dump(exclude_unset=True)
    prices = payload.pop("prices", None)

    for field, value in payload.items():
        setattr(plan, field, value)

    # When prices are provided, replace the whole set (delete-orphan handles removals).
    if prices is not None:
        plan.prices.clear()
        for p in prices:
            plan.prices.append(PlanPrice(currency=p["currency"].upper(), amount=p["amount"]))

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Plan name already exists")
    return await _get_plan_with_prices(db, plan_id)


@router.delete("/{plan_id}")
async def delete_plan(plan_id: UUID, db: AsyncSession = Depends(get_db), admin=Depends(require_admin)):
    plan = await _get_plan_with_prices(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    try:
        await db.delete(plan)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Plan is referenced by subscriptions; deactivate it instead of deleting",
        )
    return {"status": "deleted"}
