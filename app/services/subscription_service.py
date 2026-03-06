from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from app.db.models.subscription import Subscription
from app.db.models.plan import Plan
from app.db.models.invoice import Invoice
from app.db.models.enums import SubscriptionStatus, InvoiceStatus
from app.core.config import settings


class SubscriptionService:

    @staticmethod
    async def create_subscription(db: AsyncSession, user_id, plan_id):
        result = await db.execute(select(Plan).where(Plan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan or not plan.is_active:
            raise ValueError("Plan not found or inactive")

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError("User already has active subscription")

        now = datetime.utcnow()
        period_end = now + timedelta(days=30)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            status=SubscriptionStatus.active,
            current_period_start=now,
            current_period_end=period_end,
        )

        db.add(subscription)
        await db.flush()  

        invoice = Invoice(
            user_id=user_id,
            subscription_id=subscription.id,
            amount=plan.price,
            currency=plan.currency,
            status=InvoiceStatus.open,
            due_date=period_end,
        )

        db.add(invoice)

        await db.commit()
        await db.refresh(subscription)
        await db.refresh(subscription, ["plan"])

        return subscription
    
    @staticmethod
    async def get_subscriptions(db):

        result = await db.execute(select(Subscription))

        return result.scalars().all

    @staticmethod
    async def get_user_subscription(db, user_id):

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id
            )
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def cancel_subscription(db, subscription, immediate: bool = False):

        if subscription.status != SubscriptionStatus.active:
            raise ValueError("Subscription is not active")

        if immediate:
            subscription.status = SubscriptionStatus.canceled
            subscription.canceled_at = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True

        await db.commit()
        await db.refresh(subscription)

        return subscription

    @staticmethod
    async def expire_subscriptions(db):
        now = datetime.utcnow()

        result = await db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.active,
                Subscription.current_period_end <= now
            )
        )

        active_subs = result.scalars().all()

        for sub in active_subs:

            invoice = Invoice(
                subscription_id=sub.id,
                amount=sub.plan.price,
                currency=sub.plan.currency,
                status=InvoiceStatus.open,
                due_date=now + timedelta(days=settings.GRACE_PERIOD_DAYS),
            )
            db.add(invoice)

            sub.status = SubscriptionStatus.past_due

            sub.current_period_end = now + timedelta(
                days=settings.GRACE_PERIOD_DAYS
            )

        result = await db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.past_due,
                Subscription.current_period_end <= now
            )
        )

        past_due_subs = result.scalars().all()

        for sub in past_due_subs:
            if sub.cancel_at_period_end:
                sub.status = SubscriptionStatus.canceled

        await db.commit()