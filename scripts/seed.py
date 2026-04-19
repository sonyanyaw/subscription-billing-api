import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.db.models.plan import Plan


plans_data = [
    {
        "name": "Free",
        "price": 0.0,
        "currency": "USD",
        "api_limit": 1000,
        "is_active": True,
    },
    {
        "name": "Pro",
        "price": 29.99,
        "currency": "USD",
        "api_limit": 10000,
        "is_active": True,
    },
    {
        "name": "Enterprise",
        "price": 99.99,
        "currency": "USD",
        "api_limit": 100000,
        "is_active": True,
    },
]


async def seed_plans():
    async with AsyncSessionLocal() as session:
        for plan_data in plans_data:
            result = await session.execute(
                select(Plan).where(Plan.name == plan_data["name"])
            )
            existing_plan = result.scalar_one_or_none()
            if not existing_plan:
                plan = Plan(**plan_data)
                session.add(plan)
        await session.commit()
        print("Seed plans completed ✅")


if __name__ == "__main__":
    asyncio.run(seed_plans())