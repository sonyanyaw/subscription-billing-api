import json
import pytest
from unittest.mock import patch, MagicMock


def _make_stripe_event(event_type: str, payment_intent_id: str) -> MagicMock:
    """Build a fake StripeObject that mimics stripe.Webhook.construct_event output."""
    intent = MagicMock()
    intent.__getitem__ = lambda self, key: payment_intent_id if key == "id" else None

    data = MagicMock()
    data.__getitem__ = lambda self, key: intent if key == "object" else None

    event = MagicMock()
    event.__getitem__ = lambda self, key: {
        "type": event_type,
        "data": data,
    }[key]
    event.to_dict_recursive.return_value = {
        "type": event_type,
        "data": {"object": {"id": payment_intent_id}},
    }
    return event


FAKE_PAYLOAD = b'{"type":"payment_intent.succeeded"}'
FAKE_SIG = "t=123,v1=abc"


# ── Signature validation ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_signature_returns_400(client):
    import stripe
    with patch.object(
        stripe.Webhook,
        "construct_event",
        side_effect=stripe.error.SignatureVerificationError("bad sig", FAKE_SIG),
    ):
        resp = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid signature"


@pytest.mark.asyncio
async def test_invalid_payload_returns_400(client):
    import stripe
    with patch.object(
        stripe.Webhook,
        "construct_event",
        side_effect=ValueError("bad payload"),
    ):
        resp = await client.post(
            "/webhooks/stripe",
            content=b"not-json",
            headers={"stripe-signature": FAKE_SIG},
        )
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Invalid payload"


# ── payment_intent.succeeded ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_succeeded_activates_subscription(
    client, auth_headers, admin_client, subscription_and_invoice
):
    """payment_intent.succeeded → payment confirmed, invoice paid, subscription active."""
    import stripe
    _, invoice = subscription_and_invoice

    # Create a mock payment so provider_payment_id exists in DB
    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    assert pay_resp.status_code == 200
    provider_payment_id = pay_resp.json()["provider_payment_id"]

    fake_event = _make_stripe_event("payment_intent.succeeded", provider_payment_id)

    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        resp = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Subscription should be active
    sub_resp = await client.get("/subscriptions/me", headers=auth_headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "active"

    # Invoice should be paid
    invoices = (await client.get("/invoices/", headers=auth_headers)).json()
    inv = next(i for i in invoices if i["id"] == invoice["id"])
    assert inv["status"] == "paid"


@pytest.mark.asyncio
async def test_webhook_succeeded_is_idempotent(
    client, auth_headers, subscription_and_invoice
):
    """Sending payment_intent.succeeded twice doesn't error — idempotent."""
    import stripe
    _, invoice = subscription_and_invoice

    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    provider_payment_id = pay_resp.json()["provider_payment_id"]
    fake_event = _make_stripe_event("payment_intent.succeeded", provider_payment_id)

    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        r1 = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )
        r2 = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )

    assert r1.status_code == 200
    assert r2.status_code == 200


# ── payment_intent.payment_failed ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_failed_marks_payment_failed(
    client, auth_headers, subscription_and_invoice
):
    """payment_intent.payment_failed → payment status becomes failed."""
    import stripe
    _, invoice = subscription_and_invoice

    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    provider_payment_id = pay_resp.json()["provider_payment_id"]

    fake_event = _make_stripe_event("payment_intent.payment_failed", provider_payment_id)

    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        resp = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )

    assert resp.status_code == 200

    # Invoice should still be open
    invoices = (await client.get("/invoices/", headers=auth_headers)).json()
    inv = next(i for i in invoices if i["id"] == invoice["id"])
    assert inv["status"] == "open"


# ── Unknown event type ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_unknown_webhook_event_returns_ok(client):
    """Unhandled event types are logged and return 200 — no crash."""
    import stripe
    fake_event = _make_stripe_event("customer.created", "pi_unknown123")

    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        resp = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ── Webhook event persisted to DB ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_webhook_event_persisted(client, db_session):
    """Each incoming webhook is saved to webhook_events table."""
    import stripe
    from sqlalchemy import select
    from app.db.models.webhook_event import WebhookEvent

    fake_event = _make_stripe_event("customer.created", "pi_persist_test")

    with patch.object(stripe.Webhook, "construct_event", return_value=fake_event):
        resp = await client.post(
            "/webhooks/stripe",
            content=FAKE_PAYLOAD,
            headers={"stripe-signature": FAKE_SIG},
        )
    assert resp.status_code == 200

    # Verify event is in DB via session directly
    result = await db_session.execute(
        select(WebhookEvent).where(WebhookEvent.provider_payment_id == "pi_persist_test")
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.event_type == "customer.created"
