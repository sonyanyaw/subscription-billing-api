import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import AsyncSessionLocal
from app.db.models.plan import Plan
from app.db.models.plan_price import PlanPrice


plans_data = [
    {
        "name": "Free",
        "api_limit": 1000,
        "is_active": True,
        "prices": [
            {"currency": "USD", "amount": 0.0},
            {"currency": "RUB", "amount": 0.0},
        ],
    },
    {
        "name": "Pro",
        "api_limit": 10000,
        "is_active": True,
        "prices": [
            {"currency": "USD", "amount": 29.99},
            {"currency": "RUB", "amount": 2990.0},
        ],
    },
    {
        "name": "Enterprise",
        "api_limit": 100000,
        "is_active": True,
        "prices": [
            {"currency": "USD", "amount": 99.99},
            {"currency": "RUB", "amount": 9990.0},
        ],
    },
]


async def seed_plans():
    async with AsyncSessionLocal() as session:
        for plan_data in plans_data:
            prices = plan_data.pop("prices")

            result = await session.execute(
                select(Plan)
                .where(Plan.name == plan_data["name"])
                .options(selectinload(Plan.prices))
            )
            plan = result.scalar_one_or_none()

            if not plan:
                plan = Plan(**plan_data)
                session.add(plan)

            existing_currencies = {p.currency for p in plan.prices}
            for price in prices:
                if price["currency"] not in existing_currencies:
                    plan.prices.append(PlanPrice(**price))

        await session.commit()
        print("Seed plans completed ✅")


if __name__ == "__main__":
    asyncio.run(seed_plans())
