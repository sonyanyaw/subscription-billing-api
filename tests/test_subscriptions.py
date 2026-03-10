import pytest


@pytest.mark.asyncio
async def test_create_subscription_requires_auth(client):

    response = await client.post(
        "/subscriptions/",
        json={"plan_id": "test"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_subscription_requires_auth(client):

    response = await client.get("/subscriptions/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_subscription(client, auth_headers):

    response = await client.get(
        "/subscriptions/me",
        headers=auth_headers
    )

    assert response.status_code in (200, 404)