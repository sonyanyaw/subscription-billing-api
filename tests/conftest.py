import os
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from httpx import AsyncClient, ASGITransport

from app.db.models.plan import Plan
from app.main import app
from app.db.models.base import Base
from app.api.deps import get_db


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

    payload = {
        "email": "fixture@test.com",
        "password": "password123"
    }

    await client.post("/auth/register", json=payload)

    return payload


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):

    response = await client.post(
        "/auth/login",
        json=registered_user
    )

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }