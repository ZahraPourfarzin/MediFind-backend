from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # تنظیمات دیتابیس
    DB_SERVER: str = "localhost"
    DB_NAME: str = "medifind"
    DB_USER: Optional[str] = "root"  # پیش‌فرض در XAMPP معمولاً root است
    DB_PASSWORD: Optional[str] = ""   # پیش‌فرض در XAMPP معمولاً خالی است

    # سایر تنظیمات
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    UPLOAD_DIR: str = "uploads/prescriptions"
    gapgpt_api_key: str = ""

    @property
    def DATABASE_URL(self) -> str:
        # ایجاد آدرس کانکشن برای MySQL با استفاده از mysql-connector
        # فرمت: mysql+mysqlconnector://user:password@host/db_name
        return f"mysql+mysqlconnector://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "ignore"

# ایجاد یک نمونه از تنظیمات برای استفاده در کل پروژه
settings = Settings()