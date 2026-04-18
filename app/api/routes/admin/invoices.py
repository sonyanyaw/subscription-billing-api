from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.invoice import InvoiceOut
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/admin/invoices", tags=["admin/invoices"])


@router.get("/", response_model=list[InvoiceOut], status_code=200)
async def list_invoices(
    limit: int = 50, 
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin)
):
    return await InvoiceService.get_all_invoices(db, limit, offset)
