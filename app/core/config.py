from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",  
        case_sensitive=False  
    )


settings = Settings()
