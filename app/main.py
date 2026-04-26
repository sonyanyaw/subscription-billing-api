import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.subscription_service import SubscriptionService
from app.api.routes import auth, plans, users, invoices, subscriptions, payments, usage, webhooks
from app.api.routes.admin import payments as admin_payments, subscriptions as admin_subscriptions, invoices as admin_invoices


logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Subscription & Billing API")

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

app.include_router(webhooks.router)

app.include_router(admin_subscriptions.router)
app.include_router(admin_payments.router)
app.include_router(admin_invoices.router)


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


@app.get("/health")
async def health():
    return {"status": "ok"}