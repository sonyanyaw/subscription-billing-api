from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.subscription import SubscriptionWithUserOut, SubscriptionOut
from app.db.models.enums import SubscriptionStatus
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/admin/subscriptions", tags=["admin/subscriptions"])

@router.get("/", response_model=list[SubscriptionOut])
async def list_subscriptions(
    status: SubscriptionStatus | None = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin),
):
    return await SubscriptionService.get_list_subscriptions(db, status, limit, offset)


@router.get("/subscribers", response_model=list[SubscriptionWithUserOut])
async def get_subscribers(
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin)
):
    return await SubscriptionService.get_active_subscribers(db, limit, offset)