import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = "Sneaker Shop API"
    database_url: str = "sqlite:///./app.db"
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "development-secret-key"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    admin_email: str = "2219757@talnet.com"
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://sneaker-shop-ck.netlify.app"
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
    frontend_url: str = "http://localhost:5173"
    stripe_currency: str = "eur"


settings = Settings()
