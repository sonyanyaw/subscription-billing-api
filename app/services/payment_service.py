from fastapi import HTTPException, status
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.db.models.invoice import Invoice
from app.db.models.payment import Payment
from app.db.models.enums import InvoiceStatus, PaymentProvider, PaymentStatus, SubscriptionStatus
from app.core.config import settings
from app.payments.factory import get_provider


class PaymentService:

    @staticmethod
    async def create_payment(
        db: AsyncSession, 
        invoice_id: uuid.UUID, 
        provider: PaymentProvider,
        user_id: uuid.UUID
    ):

        result = await db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(selectinload(Invoice.subscription))
        )

        invoice = result.scalar_one_or_none()

        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        
        if invoice.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        if invoice.status == InvoiceStatus.paid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice already paid")

        result = await db.execute(
            select(Payment).where(
                Payment.invoice_id == invoice_id,
                Payment.status == PaymentStatus.pending
            )
        )

        existing_payment = result.scalar_one_or_none()

        if existing_payment:
            return existing_payment
        
        provider_impl = get_provider(provider)
         
        provider_payment = await provider_impl.create_payment(invoice)

        payment = Payment(
            invoice_id=invoice_id,
            provider=provider,
            provider_payment_id=provider_payment["provider_payment_id"],
            status=PaymentStatus.pending
        )

        payment.confirmation_url = provider_payment["confirmation_url"]

        db.add(payment)

        await db.commit()
        await db.refresh(payment)

        return payment
    

    @staticmethod
    async def handle_stripe_success(
        db: AsyncSession,
        provider_payment_id: str
    ):

        result = await db.execute(
            select(Payment)
            .where(Payment.provider_payment_id == provider_payment_id)
            .options(
                selectinload(Payment.invoice).selectinload(Invoice.subscription)
            )
        )

        payment = result.scalar_one_or_none()

        if not payment:
            print("Payment not found")
            return

        if payment.status == PaymentStatus.succeeded:
            return

        payment.status = PaymentStatus.succeeded

        invoice = payment.invoice
        invoice.status = InvoiceStatus.paid
        invoice.paid_at = datetime.utcnow()

        subscription = invoice.subscription

        now = datetime.utcnow()

        subscription.status = SubscriptionStatus.active
        subscription.current_period_start = now
        subscription.current_period_end = now + timedelta(
            days=settings.BILLING_PERIOD_DAYS
        )

        await db.commit()

    @staticmethod
    async def handle_stripe_failed(
        db: AsyncSession,
        provider_payment_id: str
    ):

        result = await db.execute(
            select(Payment).where(
                Payment.provider_payment_id == provider_payment_id
            )
        )

        payment = result.scalar_one_or_none()

        if not payment:
            return

        payment.status = PaymentStatus.failed

        await db.commit()


    @staticmethod
    async def get_all_payments(
        db: AsyncSession,
        limit: int,
        offset: int
    ):

        result = await db.execute(
            select(Payment)
            .options(selectinload(Payment.invoice))
            .limit(limit)
            .offset(offset)
        )

        return result.scalars().all()
