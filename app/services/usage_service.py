from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.api_usage import APIUsage
from app.db.models.subscription import Subscription
from app.db.models.enums import SubscriptionStatus


class UsageService:

    @staticmethod
    async def get_or_create_usage(
        db: AsyncSession,
        user_id,
        period_start,
        period_end
    ):
        result = await db.execute(
            select(APIUsage).where(
                APIUsage.user_id == user_id,
                APIUsage.period_start == period_start,
                APIUsage.period_end == period_end
            )
        )

        usage = result.scalar_one_or_none()

        if usage:
            return usage

        usage = APIUsage(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            requests_count=0
        )

        db.add(usage)
        await db.flush()

        return usage

    @staticmethod
    async def increment_usage(db: AsyncSession, usage: APIUsage):

        await db.execute(
            update(APIUsage)
            .where(APIUsage.id == usage.id)
            .values(
                requests_count=APIUsage.requests_count + 1
            )
        )
        # usage.requests_count += 1
        # await db.flush()