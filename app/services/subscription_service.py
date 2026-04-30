from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found or inactive")

        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == user_id,
                Subscription.status.in_([
                    SubscriptionStatus.incomplete,
                    SubscriptionStatus.active,
                    SubscriptionStatus.past_due
                ])
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if existing.status == SubscriptionStatus.incomplete:
                result = await db.execute(
                    select(Subscription)
                    .where(Subscription.id == existing.id)
                    .options(selectinload(Subscription.plan))
                )
                return result.scalar_one()
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a subscription")

        now = datetime.utcnow()
        period_end = now + timedelta(days=30)

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            status=SubscriptionStatus.incomplete,
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

        result = await db.execute(
            select(Subscription)
            .where(Subscription.id == subscription.id)
            .options(selectinload(Subscription.plan))
        )

        subscription = result.scalar_one()

        return subscription
    
    @staticmethod
    async def get_subscriptions(db):

        result = await db.execute(select(Subscription))

        return result.scalars().all()

    @staticmethod
    async def get_user_subscription(db, user_id):

        result = await db.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.active
            )
            .options(selectinload(Subscription.plan))
        )

        return result.scalar_one_or_none()

    @staticmethod
    async def get_subscription_by_id(db: AsyncSession, subscription_id, user_id=None):
        query = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(Subscription.id == subscription_id)
        )
        if user_id is not None:
            query = query.where(Subscription.user_id == user_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession, 
        subscription_id: UUID, 
        immediate: bool = False, 
        user_id: UUID = None,
    ):

        subscription = await SubscriptionService.get_subscription_by_id(db, subscription_id, user_id)

        if not subscription:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")

        if subscription.status != SubscriptionStatus.active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription is not active")

        if immediate:
            subscription.status = SubscriptionStatus.canceled
            subscription.canceled_at = datetime.utcnow()
        else:
            subscription.cancel_at_period_end = True

        await db.commit()
        await db.refresh(subscription, ["plan"])

        return subscription

    @staticmethod
    async def expire_subscriptions(db: AsyncSession):
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



    @staticmethod
    async def get_list_subscriptions(
        db: AsyncSession,
        status: Optional[SubscriptionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ):
        query = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan),
                selectinload(Subscription.user),
            )
            .limit(limit)
            .offset(offset)
        )

        if status:
            query = query.where(Subscription.status == status)

        result = await db.execute(query)

        return result.scalars().all()

    @staticmethod
    async def get_active_subscribers(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ):
        result = await db.execute(
            select(Subscription)
            .where(Subscription.status == SubscriptionStatus.active)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.plan),
            )
            .limit(limit)
            .offset(offset)
        )

        return result.scalars().all()
