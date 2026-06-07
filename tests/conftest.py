import os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from httpx import AsyncClient, ASGITransport

from app.db.models.plan import Plan
from app.db.models.user import User
from app.db.models.enums import UserRole
from app.main import app
from app.db.models.base import Base
from app.api.deps import get_db
from app.core.security import hash_password


TEST_DATABASE_URL = os.getenv("DATABASE_URL")


@pytest_asyncio.fixture
async def engine():

    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):

    TestingSessionLocal = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with TestingSessionLocal() as session:
        yield session

        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())

        await session.commit()


@pytest_asyncio.fixture
async def seeded_plans(db_session):

    plans = [
        Plan(name="Free",       price=0.0,  currency="USD", api_limit= 1000, is_active=True),
        Plan(name="Pro",        price=29.99, currency="USD", api_limit= 1000, is_active=True),
        Plan(name="Enterprise", price=99.99, currency="USD", api_limit= 1000, is_active=True),
    ]
    
    db_session.add_all(plans)
    await db_session.commit()
    return plans


@pytest_asyncio.fixture
async def client(db_session):

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(client):
    payload = {"email": "fixture@test.com", "password": "password123"}
    await client.post("/auth/register", json=payload)
    return payload


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):
    response = await client.post("/auth/login", json=registered_user)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_client(db_session):
    """
    HTTP client with admin privileges via dependency override.
    Bypasses require_admin auth check so DB session stays clean.
    Uses the same db_session as the regular client.
    """
    from app.api.deps import require_admin

    async def override_get_db():
        yield db_session

    def override_require_admin():
        # Return a minimal admin-like object — only role is checked downstream
        return User(email="admin@override.test", role=UserRole.admin)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_admin] = override_require_admin

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_headers(client, db_session):
    """Register a user via HTTP, promote to admin in DB, return auth headers."""
    creds = {"email": "admin@test.com", "password": "adminpass123"}
    await client.post("/auth/register", json=creds)

    result = await db_session.execute(select(User).where(User.email == creds["email"]))
    user = result.scalar_one()
    user.role = UserRole.admin
    await db_session.commit()

    resp = await client.post("/auth/login", json=creds)
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def subscription_and_invoice(client, auth_headers, seeded_plans):
    """Creates a subscription and returns (subscription, invoice) dicts."""
    plan_id = str(seeded_plans[1].id)  # Pro plan

    sub_resp = await client.post(
        "/subscriptions/",
        json={"plan_id": plan_id},
        headers=auth_headers,
    )
    assert sub_resp.status_code == 200
    sub = sub_resp.json()

    inv_resp = await client.get("/invoices/", headers=auth_headers)
    assert inv_resp.status_code == 200
    invoices = inv_resp.json()
    open_inv = next(i for i in invoices if i["status"] == "open")

    return sub, open_inv