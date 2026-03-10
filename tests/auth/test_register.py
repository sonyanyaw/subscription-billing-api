import pytest
import uuid

def random_email():
    return f"{uuid.uuid4()}@example.com"


@pytest.mark.asyncio
async def test_register_success(client):

    email = random_email()
    response = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "password123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email


@pytest.mark.asyncio
async def test_register_duplicate_email(client):

    payload = {
        "email": "dup@test.com",
        "password": "password123"
    }

    await client.post("/auth/register", json=payload)

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_register_short_password(client):

    response = await client.post(
        "/auth/register",
        json={
            "email": "short@test.com",
            "password": "123"
        }
    )

    assert response.status_code == 422