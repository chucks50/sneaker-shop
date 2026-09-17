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
    admin_email: str = "admin@example.com"
    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
