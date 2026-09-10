from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Sneaker Shop API"
    database_url: str = "postgresql+psycopg2://postgres:postgres@db:5432/sneaker_shop"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
