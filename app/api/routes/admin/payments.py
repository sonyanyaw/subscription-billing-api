from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.payment import PaymentOut
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/admin/payments", tags=["admin/payments"])


@router.get("/", response_model=list[PaymentOut])
async def all_payments(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    return await PaymentService.get_all_payments(db, limit, offset)


@router.patch("/{payment_id}/confirm", status_code=200)
async def confirm_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    await PaymentService.confirm_payment(db, payment_id)
    return {"status": "confirmed"}


@router.patch("/{payment_id}/fail", status_code=200)
async def fail_payment(
    payment_id: UUID,
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    await PaymentService.fail_payment(db, payment_id)
    return {"status": "failed"}