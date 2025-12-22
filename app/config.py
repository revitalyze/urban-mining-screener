import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings."""

    load_dotenv()  # Load .env file if present
    # Database settings
    # default value for db_user is "user"
    DB_USER: str = os.getenv("DB_USER", "user")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "ums_db")
    DB_HOST: str = os.getenv("DB_HOST", "postgres")
    DB_PORT: int = int(os.getenv("DB_PORT", 5432))

    # Construct DATABASE_URL from individual components
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )

    # Application settings
    APP_NAME: str = "Building Materials Estimator"
    APP_VERSION: str = "0.1.0"

    # Security settings (do not read .env directly in code; rely on process env in deployment)
    APP_PASSWORD: str | None = os.getenv("APP_PASSWORD")
    AUTH_SECRET: str | None = os.getenv("AUTH_SECRET")

    # Environment flag to control cookie security, etc.
    ENV: str = os.getenv("ENV", "development")

    class Config:
        env_file = ".env"
        # Allow extra fields to prevent validation errors
        extra = "allow"


settings = Settings()

# Validate presence of required secrets to avoid insecure runs
_missing = []
if not settings.APP_PASSWORD:
    _missing.append("APP_PASSWORD")
if not settings.AUTH_SECRET:
    _missing.append("AUTH_SECRET")

if _missing:
    # Fail fast with a clear message; operators should set these via environment (Docker/CI/Production)
    raise RuntimeError(f"Missing required environment variables: {', '.join(_missing)}")
