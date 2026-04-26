from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.subscription_service import SubscriptionService
from app.api.routes import auth, plans, users, invoices, subscriptions, payments, usage, webhooks
from app.api.routes.admin import payments as admin_payments, subscriptions as admin_subscriptions, invoices as admin_invoices



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

@app.on_event("startup")
async def startup_event():
    try:
        async with AsyncSessionLocal() as db:
            await SubscriptionService.expire_subscriptions(db)
    except Exception as e:
        print("Startup skipped expire_subscriptions:", e)


@app.get("/health")
async def health():
    return {"status": "ok"}