import pytest


@pytest.mark.asyncio
async def test_login_success(client):

    await client.post(
        "/auth/register",
        json={
            "email": "login@test.com",
            "password": "password123"
        }
    )

    response = await client.post(
        "/auth/login",
        json={
            "email": "login@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):

    await client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "password": "password123"
        }
    )

    response = await client.post(
        "/auth/login",
        json={
            "email": "user@test.com",
            "password": "wrongpass"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_user_not_found(client):

    response = await client.post(
        "/auth/login",
        json={
            "email": "missing@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == 401
    

@pytest.mark.asyncio
async def test_protected_route(client, auth_headers):

    response = await client.get(
        "/users/me",
        headers=auth_headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_without_token(client):

    response = await client.get("/users/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_invalid_token(client):

    response = await client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalidtoken"
        }
    )

    assert response.status_code == 401
    

@pytest.mark.asyncio
async def test_token_allows_access(client, auth_headers):

    response = await client.get(
        "/users/me",
        headers=auth_headers
    )

    data = response.json()

    assert response.status_code == 200
    assert "email" in data


@pytest.mark.asyncio
async def test_password_not_returned(client):

    response = await client.post(
        "/auth/register",
        json={
            "email": "secure@test.com",
            "password": "password123"
        }
    )

    data = response.json()

    assert "password" not in data