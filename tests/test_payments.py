import pytest
import uuid


@pytest.mark.asyncio
async def test_create_payment_requires_auth(client):

    response = await client.post(
        "/payments/",
        json={
            "invoice_id": "test",
            "provider": "stripe"
        }
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_confirm_payment_requires_admin(client):

    fake_id = str(uuid.uuid4())

    response = await client.patch(
        f"/admin/payments/{fake_id}/confirm"
    )

    assert response.status_code == 401
    