import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.webhook_event import WebhookEvent
from app.db.models.enums import WebhookEventStatus


class WebhookEventService:

    @staticmethod
    async def log(
        db: AsyncSession,
        event_type: str,
        provider_payment_id: str | None = None,
        status: WebhookEventStatus = WebhookEventStatus.received,
        payload: dict | None = None,
    ) -> WebhookEvent:
        event = WebhookEvent(
            event_type=event_type,
            provider_payment_id=provider_payment_id,
            status=status,
            payload=json.dumps(payload) if payload else None,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_all(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WebhookEvent]:
        result = await db.execute(
            select(WebhookEvent)
            .order_by(WebhookEvent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
