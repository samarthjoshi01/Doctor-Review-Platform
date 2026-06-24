# config/settings.py  –  Centralised app settings via Pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongo_uri: str
    mongo_db_name: str = "docreview_db"

    # Dev convenience
    skip_db: bool = False

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    environment: str = "development"

    # CORS
    client_origin: str = "http://127.0.0.1:5500"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()          # singleton – read .env only once
def get_settings() -> Settings:
    return Settings()
