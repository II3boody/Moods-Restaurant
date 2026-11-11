import re
from functools import lru_cache

from pydantic import field_validator, model_validator
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
    # بديل: المتغير الرسمي من Cloudinary بالشكل cloudinary://<api_key>:<api_secret>@<cloud_name>
    CLOUDINARY_URL: str = ""

    @field_validator("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET",
                     "CLOUDINARY_FOLDER", "CLOUDINARY_URL", mode="before")
    @classmethod
    def _clean_cloudinary(cls, v):
        """بيشيل المسافات والـ tab والـ newline وعلامات التنصيص والحروف المخفية (zero-width) اللي بتتنسخ مع القيمة."""
        if isinstance(v, str):
            v = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2060\ufeff]", "", v)
            return v.strip().strip("\"'").strip().strip("/")
        return v

    @model_validator(mode="after")
    def _fill_from_cloudinary_url(self):
        """لو CLOUDINARY_URL موجود، بيكمّل منه أي قيمة ناقصة أو اسم cloud غلط."""
        m = re.fullmatch(r"cloudinary://([^:@/\s]+):([^@/\s]+)@([A-Za-z0-9_-]+)", self.CLOUDINARY_URL or "")
        if m:
            if not self.CLOUDINARY_API_KEY:
                self.CLOUDINARY_API_KEY = m.group(1)
            if not self.CLOUDINARY_API_SECRET:
                self.CLOUDINARY_API_SECRET = m.group(2)
            if not re.fullmatch(r"[A-Za-z0-9_-]+", self.CLOUDINARY_CLOUD_NAME or ""):
                self.CLOUDINARY_CLOUD_NAME = m.group(3)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
