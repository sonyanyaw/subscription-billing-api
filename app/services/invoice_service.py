from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.invoice import Invoice


class InvoiceService:

    @staticmethod
    async def get_invoices(
        db: AsyncSession, 
        user_id: UUID
    ):
        result = await db.execute(
            select(Invoice).where(
                Invoice.user_id == user_id
            )
        )

        return result.scalars().all()
    
    
    @staticmethod
    async def get_one_invoice(
        db: AsyncSession, 
        invoice_id: int, 
        user_id: int
    ):
        result = await db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.user_id == user_id
            )
        )

        return result.scalar_one_or_none()


    @staticmethod
    async def get_all_invoices(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ):
        result = await db.execute(
            select(Invoice)
            .limit(limit)
            .offset(offset)
        )

        return result.scalars().all()