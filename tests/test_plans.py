import pytest


@pytest.mark.asyncio
async def test_list_plans(client, seeded_plans):

    response = await client.get("/plans/")

    assert response.status_code == 200
    assert len(response.json()) == len(seeded_plans)