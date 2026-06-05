from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, require_admin
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billings", tags=["billing"])

@router.post("/billing/run")
async def run_billing(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    await BillingService.process_renewals(db)
    await BillingService.process_grace_expirations(db)
    return {"status": "billing processed"}