from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_current_user, get_db
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import SubscriptionCreate, SubscriptionOut
from app.db.models.user import User


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.post("/", response_model=SubscriptionOut)
async def create_subscription(
    data: SubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        subscription = await SubscriptionService.create_subscription(
            db, current_user.id, data.plan_id
        )
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=SubscriptionOut)
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    subscription = await SubscriptionService.get_user_subscription(
        db,
        current_user.id
    )

    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    
    return subscription


@router.post("/{subscription_id}/cancel", response_model=SubscriptionOut)
async def cancel_subscription(
    subscription_id: UUID,
    immediate: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await SubscriptionService.cancel_subscription(
        db, subscription_id, immediate, user_id=current_user.id
    )