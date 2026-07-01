from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Supabase / PostgreSQL
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/lottery"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "https://project05.vercel.app"]

    # Export
    EXPORT_DIR: str = "/opt/lottery/exports"

    class Config:
        env_file = ".env"


settings = Settings()
