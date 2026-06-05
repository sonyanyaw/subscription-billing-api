from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models.subscription import Subscription
from app.db.models.invoice import Invoice
from app.db.models.enums import (
    SubscriptionStatus,
    InvoiceStatus,
)
from app.core.config import settings


class BillingService:

    @staticmethod
    async def process_renewals(db):

        now = datetime.utcnow()

        result = await db.execute(
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                Subscription.status == SubscriptionStatus.active,
                Subscription.current_period_end <= now,
            )
        )

        subscriptions = result.scalars().all()

        for sub in subscriptions:

            invoice = Invoice(
                user_id=sub.user_id,
                subscription_id=sub.id,
                amount=sub.plan.price,
                currency=sub.plan.currency,
                status=InvoiceStatus.open,
                due_date=now + timedelta(days=settings.GRACE_PERIOD_DAYS),
            )
            db.add(invoice)

            # переводим в past_due
            sub.status = SubscriptionStatus.past_due
            sub.current_period_end = now + timedelta(
                days=settings.GRACE_PERIOD_DAYS
            )

        await db.commit()


    @staticmethod
    async def process_grace_expirations(db):

        now = datetime.utcnow()

        result = await db.execute(
            select(Subscription).where(
                Subscription.status == SubscriptionStatus.past_due,
                Subscription.current_period_end <= now
            )
        )

        subs = result.scalars().all()

        for sub in subs:
            sub.status = SubscriptionStatus.canceled

        await db.commit()