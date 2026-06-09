from datetime import timedelta
from app.core.utils import utcnow

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.db.models.enums import SubscriptionStatus
from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.user import User


@pytest_asyncio.fixture
async def limited_subscription_headers(client, db_session):
    """User with an active subscription that has api_limit=1."""
    creds = {"email": "limited@test.com", "password": "password123"}
    await client.post("/auth/register", json=creds)

    result = await db_session.execute(select(User).where(User.email == creds["email"]))
    user = result.scalar_one()

    plan = Plan(name="Nano", price=0.0, currency="USD", api_limit=1, is_active=True)
    db_session.add(plan)
    await db_session.flush()

    now = utcnow()
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status=SubscriptionStatus.active,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    db_session.add(sub)
    await db_session.commit()

    resp = await client.post("/auth/login", json=creds)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_request_within_limit_passes(client, limited_subscription_headers):
    """First request is within the limit — should succeed."""
    resp = await client.get("/users/me", headers=limited_subscription_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_request_over_limit_returns_429(client, limited_subscription_headers):
    """After exhausting api_limit=1, next request gets 429."""
    await client.get("/users/me", headers=limited_subscription_headers)  # count=1, allowed
    resp = await client.get("/users/me", headers=limited_subscription_headers)  # count=2, blocked
    assert resp.status_code == 429
    assert resp.json()["detail"] == "API limit exceeded"


@pytest.mark.asyncio
async def test_no_subscription_passes_through(client, auth_headers):
    """User without active subscription is not blocked — route handles auth only."""
    resp = await client.get("/users/me", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_unauthenticated_not_rate_limited(client):
    """Unauthenticated request reaches auth gate (401), not the rate limiter."""
    resp = await client.get("/users/me")
    assert resp.status_code == 401
