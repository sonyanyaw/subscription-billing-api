import pytest


@pytest.mark.asyncio
async def test_access_with_valid_token(client, auth_headers):

    response = await client.get(
        "/users/me",
        headers=auth_headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_access_without_token(client):

    response = await client.get("/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_with_invalid_token(client):

    response = await client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalidtoken"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_with_wrong_scheme(client):

    response = await client.get(
        "/users/me",
        headers={
            "Authorization": "Token 123"
        }
    )

    assert response.status_code == 401
    