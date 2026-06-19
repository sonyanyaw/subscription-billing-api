from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException

from app.db.models.subscription import Subscription
from app.db.models.enums import SubscriptionStatus


class UsageLimiterService:

    @staticmethod
    async def check_and_increment(db: AsyncSession, user_id):
        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active,
            )
            .options(selectinload(Subscription.plan))
        )

        subscription = result.scalar_one_or_none()

        if not subscription:
            return  # no active subscription — skip rate limiting

        limit = subscription.plan.api_limit

        result = await db.execute(
            text("""
                INSERT INTO api_usage (id, user_id, period_start, period_end, requests_count)
                VALUES (gen_random_uuid(), :user_id, :period_start, :period_end, 1)
                ON CONFLICT (user_id, period_start, period_end)
                DO UPDATE SET requests_count = api_usage.requests_count + 1
                RETURNING requests_count
            """),
            {
                "user_id": str(user_id),
                "period_start": subscription.current_period_start,
                "period_end": subscription.current_period_end,
            },
        )

        requests_count = result.scalar_one()

        if requests_count > limit:
            raise HTTPException(status_code=429, detail="API limit exceeded")
