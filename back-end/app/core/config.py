from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "MOODS Restaurant & Cafe API"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./moods.db"

    SECRET_KEY: str = "change-me-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:3000"

    FIRST_SUPERADMIN_EMAIL: str = "superadmin@moods.com"
    FIRST_SUPERADMIN_PASSWORD: str = "ChangeMe123!"
    FIRST_SUPERADMIN_NAME: str = "Super Admin"

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@moods.com"

    UPLOAD_DIR: str = "uploads"

    # Cloudinary (لو فاضيين، الصور بتتخزن في الداتابيز زي الأول)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "moods"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
