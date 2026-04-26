from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.invoice import InvoiceOut
from app.services.invoice_service import InvoiceService


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/", response_model=list[InvoiceOut], status_code=200)
async def list_invoices(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    
    return await InvoiceService.get_invoices(db, user_id=current_user.id, limit=limit, offset=skip)


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_one_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    
    invoice = await InvoiceService.get_one_invoice(db, invoice_id, current_user.id)

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    
    return invoice
