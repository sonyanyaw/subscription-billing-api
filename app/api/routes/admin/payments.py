from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.payment import PaymentOut
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/admin/payments", tags=["admin/payments"])

@router.get("/", response_model=list[PaymentOut])
async def all_payments(
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db), 
    admin=Depends(require_admin)
):
    return await PaymentService.get_all_payments(db, limit, offset)