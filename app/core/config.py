from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    ALGORITHM: str
    GRACE_PERIOD_DAYS: int
    BILLING_PERIOD_DAYS: int

    STRIPE_SECRET_KEY: str
    STRIPE_PUBLIC_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    PAYMENT_RETURN_URL: str = "http://localhost:8000/static/dashboard.html"

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",  
        case_sensitive=False  
    )


settings = Settings()
