from sqlalchemy import select
from app.db.models.invoice import Invoice


class InvoiceService:
    @staticmethod
    async def get_invoices(db, user_id):
        result = await db.execute(
            select(Invoice).where(
                Invoice.user_id == user_id
            )
        )

        return result.scalars().all()
    
    @staticmethod
    async def get_one_invoice(db, invoice_id, user_id):
        result = await db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.user_id == user_id
            )
        )

        return result.scalar_one_or_none()