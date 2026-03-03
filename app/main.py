from fastapi import FastAPI

app = FastAPI(title="Subscription & Billing API")

@app.get("/health")
async def health():
    return {"status": "ok"}