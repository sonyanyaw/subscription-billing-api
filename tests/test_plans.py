import pytest


@pytest.mark.asyncio
async def test_list_plans(client):

    response = await client.get("/plans/")

    assert response.status_code == 200

    assert isinstance(response.json(), list)    