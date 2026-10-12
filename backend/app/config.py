from typing import List, Literal
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine backend directory and path to .env
backend_dir = Path(__file__).resolve().parent.parent
env_file_path = backend_dir / ".env"

# Explicitly load .env into environment if present
if env_file_path.exists():
    load_dotenv(dotenv_path=env_file_path, override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Employee Management System API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    APP_ENV: Literal["development", "production"] = "production"

    # Default to local SQLite only when no MySQL URL is configured
    DATABASE_URL: str = "sqlite:///./ems_local.db"

    # Allowed CORS Origins for frontend development
    CORS_ORIGINS: List[str] = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:19006",
        "http://127.0.0.1:19006",
        "http://localhost:3000",
    ]

    # Authentication secrets are supplied only by the environment/.env.  The
    # empty default deliberately keeps authentication inactive until an actual
    # secret is configured; security helpers reject it at use time.
    AUTH_JWT_SECRET_KEY: str = ""
    AUTH_JWT_ALGORITHM: Literal["HS256"] = "HS256"
    AUTH_JWT_ISSUER: str = "ems-api"
    AUTH_JWT_AUDIENCE: str = "ems-client"
    AUTH_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    AUTH_MIN_PASSWORD_LENGTH: int = 12
    AUTH_MAX_PASSWORD_LENGTH: int = 128
    AUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    AUTH_SESSION_EXPIRE_DAYS: int = 30
    AUTH_LOGIN_MAX_FAILURES: int = 5
    AUTH_LOGIN_LOCKOUT_MINUTES: int = 15
    AUTH_TRUSTED_ORIGINS: List[str] = []
    AUTH_REFRESH_COOKIE_NAME: str = "ems_refresh"
    AUTH_CSRF_COOKIE_NAME: str = "ems_csrf"
    AUTH_CSRF_HEADER_NAME: str = "X-CSRF-Token"
    AUTH_COOKIE_SECURE: bool = True
    AUTH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


settings = Settings()
