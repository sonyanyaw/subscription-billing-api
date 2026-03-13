from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.schemas.payment import PaymentCreate, PaymentOut
from app.services.payment_service import PaymentService


router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/", response_model=PaymentOut)
async def create_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return await PaymentService.create_payment(
        db=db,
        invoice_id=data.invoice_id,
        provider=data.provider,
        user_id=current_user.id
    )
