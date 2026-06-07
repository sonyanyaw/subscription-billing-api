import uuid
import pytest
from sqlalchemy import select

from app.services.payment_service import PaymentService
from app.db.models.payment import Payment


# ── Auth guards ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_payment_requires_auth(client):
    response = await client.post(
        "/payments/",
        json={"invoice_id": str(uuid.uuid4()), "provider": "mock"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirm_payment_requires_admin(client, registered_user):
    """Non-admin cannot confirm payments — must not return 200."""
    login = await client.post("/auth/login", json=registered_user)
    user_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.patch(
        f"/admin/payments/{uuid.uuid4()}/confirm",
        headers=user_headers,
    )
    assert response.status_code != 200


@pytest.mark.asyncio
async def test_fail_payment_requires_admin(client, registered_user):
    """Non-admin cannot fail payments — must not return 200."""
    login = await client.post("/auth/login", json=registered_user)
    user_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = await client.patch(
        f"/admin/payments/{uuid.uuid4()}/fail",
        headers=user_headers,
    )
    assert response.status_code != 200


# ── Full payment flow (service-level confirm/fail) ───────────────────────────

@pytest.mark.asyncio
async def test_full_payment_flow_mock(
    client, auth_headers, db_session, subscription_and_invoice
):
    """subscribe → create payment → service confirm → invoice paid → subscription active"""
    sub, invoice = subscription_and_invoice
    assert sub["status"] == "incomplete"
    assert invoice["status"] == "open"

    # User creates payment via HTTP
    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    assert pay_resp.status_code == 200
    payment = pay_resp.json()
    assert payment["status"] == "pending"

    # Confirm directly via service (same session)
    await PaymentService.confirm_payment(db_session, uuid.UUID(payment["id"]))

    # Invoice should be paid
    invoices = (await client.get("/invoices/", headers=auth_headers)).json()
    paid_invoice = next(i for i in invoices if i["id"] == invoice["id"])
    assert paid_invoice["status"] == "paid"

    # Subscription should be active
    sub_resp = await client.get("/subscriptions/me", headers=auth_headers)
    assert sub_resp.status_code == 200
    assert sub_resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_fail_payment_flow(
    client, auth_headers, db_session, subscription_and_invoice
):
    """create payment → service fail → payment failed, invoice still open"""
    _, invoice = subscription_and_invoice

    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    assert pay_resp.status_code == 200
    payment_id = uuid.UUID(pay_resp.json()["id"])

    # Fail directly via service
    await PaymentService.fail_payment(db_session, payment_id)

    # Invoice should still be open
    invoices = (await client.get("/invoices/", headers=auth_headers)).json()
    inv = next(i for i in invoices if i["id"] == invoice["id"])
    assert inv["status"] == "open"

    # Subscription still incomplete
    sub_resp = await client.get("/subscriptions/me", headers=auth_headers)
    assert sub_resp.status_code in (200, 404)
    if sub_resp.status_code == 200:
        assert sub_resp.json()["status"] == "incomplete"


# ── Idempotency ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_payment_returns_existing(
    client, auth_headers, subscription_and_invoice
):
    """Creating payment twice on same invoice returns the existing pending one."""
    _, invoice = subscription_and_invoice

    r1 = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    r2 = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


# ── Access control ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cannot_pay_other_users_invoice(
    client, seeded_plans, subscription_and_invoice
):
    """User B cannot pay User A's invoice."""
    _, invoice = subscription_and_invoice

    await client.post(
        "/auth/register",
        json={"email": "other@test.com", "password": "password123"},
    )
    other_login = await client.post(
        "/auth/login",
        json={"email": "other@test.com", "password": "password123"},
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=other_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_pay_already_paid_invoice(
    client, auth_headers, db_session, subscription_and_invoice
):
    """Paying an already-paid invoice returns 400."""
    _, invoice = subscription_and_invoice

    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    payment_id = uuid.UUID(pay_resp.json()["id"])

    # Confirm via service
    await PaymentService.confirm_payment(db_session, payment_id)

    # Try to pay again
    resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── Edge cases ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_payment_not_found(db_session):
    """Confirming non-existent payment raises 404."""
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await PaymentService.confirm_payment(db_session, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_cannot_confirm_already_confirmed_payment(
    client, auth_headers, db_session, subscription_and_invoice
):
    """Confirming an already-confirmed payment raises 400."""
    from fastapi import HTTPException
    _, invoice = subscription_and_invoice

    pay_resp = await client.post(
        "/payments/",
        json={"invoice_id": invoice["id"], "provider": "mock"},
        headers=auth_headers,
    )
    payment_id = uuid.UUID(pay_resp.json()["id"])

    await PaymentService.confirm_payment(db_session, payment_id)

    with pytest.raises(HTTPException) as exc:
        await PaymentService.confirm_payment(db_session, payment_id)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_payment_invalid_invoice_id(client, auth_headers):
    """Payment with non-existent invoice returns 404."""
    resp = await client.post(
        "/payments/",
        json={"invoice_id": str(uuid.uuid4()), "provider": "mock"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
