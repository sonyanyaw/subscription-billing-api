import pytest
import uuid


@pytest.mark.asyncio
async def test_list_invoices_requires_auth(client):

    response = await client.get("/invoices/")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_invoices(client, auth_headers):

    response = await client.get(
        "/invoices/",
        headers=auth_headers
    )

    assert response.status_code == 200

    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_invoice_not_found(client, auth_headers):

    fake_id = str(uuid.uuid4())

    response = await client.get(
        f"/invoices/{fake_id}",
        headers=auth_headers
    )

    assert response.status_code == 404