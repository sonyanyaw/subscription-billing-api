from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api.deps import get_db, require_admin
from app.db.models.user import User
from app.db.models.subscription import Subscription
from app.db.models.enums import SubscriptionStatus

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):

    users = await db.scalar(select(func.count(User.id)))
    subs = await db.scalar(select(func.count(Subscription.id)))

    active_subs = await db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status == SubscriptionStatus.active
        )
    )

    return {
        "users": users,
        "subscriptions": subs,
        "active_subscriptions": active_subs
    }