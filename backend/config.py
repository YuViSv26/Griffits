import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int
    nordrouter_api_key: str
    nordrouter_base_url: str
    nordrouter_model: str
    cors_origins: list[str]
    cookie_name: str
    cookie_secure: bool
    app_debug: bool
    frontend_url: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_ssl: bool
    yookassa_shop_id: str
    yookassa_secret_key: str
    plan_pdf_price_rub: int


@lru_cache
def get_settings() -> Settings:
    cors_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL", "sqlite+aiosqlite:///./griffiths_web.db"
        ).strip(),
        jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production").strip(),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256").strip(),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "10080")),
        nordrouter_api_key=os.getenv("NORDROUTER_API_KEY", "").strip(),
        nordrouter_base_url=os.getenv(
            "NORDROUTER_BASE_URL", "https://nordrouter.com/v1"
        ).strip().rstrip("/"),
        nordrouter_model=os.getenv(
            "NORDROUTER_MODEL", "anthropic/claude-sonnet-4.6"
        ).strip(),
        cors_origins=[o.strip() for o in cors_raw.split(",") if o.strip()],
        cookie_name=os.getenv("AUTH_COOKIE_NAME", "griffiths_token").strip(),
        cookie_secure=os.getenv("COOKIE_SECURE", "false").lower() == "true",
        app_debug=os.getenv("APP_DEBUG", "false").lower() == "true",
        frontend_url=os.getenv("FRONTEND_URL", "http://localhost:5173").strip().rstrip("/"),
        smtp_host=os.getenv("SMTP_HOST", "").strip(),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_user=os.getenv("SMTP_USER", "").strip(),
        smtp_password=(
            os.getenv("SMTP_PASSWORD", "").strip()
            or os.getenv("SMTP_PASS", "").strip()
        ),
        smtp_from=os.getenv("SMTP_FROM", "").strip(),
        smtp_use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
        yookassa_shop_id=os.getenv("YOOKASSA_SHOP_ID", "").strip(),
        yookassa_secret_key=os.getenv("YOOKASSA_SECRET_KEY", "").strip(),
        plan_pdf_price_rub=int(os.getenv("PLAN_PDF_PRICE_RUB", "199")),
    )
