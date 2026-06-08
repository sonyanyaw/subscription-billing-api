import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.subscription_service import SubscriptionService
from app.api.routes import auth, plans, users, invoices, subscriptions, payments, usage, webhooks, billings
from app.api.routes.admin import (
    payments as admin_payments,
    subscriptions as admin_subscriptions,
    invoices as admin_invoices,
    webhooks as admin_webhooks,
    plans as admin_plans,
    users as admin_users,
    stats as admin_stats,
)
from app.api.deps import check_usage_limit


logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_expire_subscriptions():
    try:
        async with AsyncSessionLocal() as db:
            await SubscriptionService.expire_subscriptions(db)
        logger.info("Scheduled expire_subscriptions completed")
    except Exception as e:
        logger.error("Scheduled expire_subscriptions failed: %s", e)


app = FastAPI(title="Subscription & Billing API", dependencies=[Depends(check_usage_limit)])

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(invoices.router)
app.include_router(subscriptions.router)
app.include_router(payments.router)
app.include_router(usage.router)
app.include_router(billings.router)

app.include_router(webhooks.router)

app.include_router(admin_subscriptions.router)
app.include_router(admin_payments.router)
app.include_router(admin_invoices.router)
app.include_router(admin_webhooks.router)
app.include_router(admin_plans.router)
app.include_router(admin_users.router)
app.include_router(admin_stats.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
async def startup_event():
    try:
        async with AsyncSessionLocal() as db:
            await SubscriptionService.expire_subscriptions(db)
    except Exception as e:
        logger.error("Startup expire_subscriptions failed: %s", e)

    scheduler.add_job(
        _run_expire_subscriptions,
        trigger="interval",
        hours=6,
        id="expire_subscriptions",
    )
    scheduler.start()
    logger.info("Scheduler started: expire_subscriptions every 6 hours")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")


@app.get("/health")
async def health():
    return {"status": "ok"}