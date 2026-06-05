from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.schemas.webhook_event import WebhookEventOut
from app.services.webhook_event_service import WebhookEventService

router = APIRouter(prefix="/admin/webhooks", tags=["admin/webhooks"])


@router.get("/", response_model=list[WebhookEventOut])
async def list_webhook_events(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    return await WebhookEventService.get_all(db, limit, offset)
