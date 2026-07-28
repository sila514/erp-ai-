"""
Uygulama genelindeki ayarlar.
.env dosyasından okunur (bkz. infra/.env.example)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Genel
    APP_NAME: str = "ERP AI Platform"
    ENV: str = "development"
    DEBUG: bool = True

    # Veritabanı
    DATABASE_URL: str = "postgresql://erp_user:erp_pass@localhost:5432/erp_db"

    # Güvenlik / JWT
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    # ML servis adresi (ayrı bir mikroservis olarak çalışır)
    ML_SERVICE_URL: str = "http://localhost:8001"

    # Event-driven mimari için Redis (Streams). Satış olayları burada yayınlanır,
    # ml_service ayrı bir consumer group ile dinler.
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Copilot icin LLM ayarlari (Google Gemini - ucretsiz kotali)
    GEMINI_API_KEY: str = ""
    COPILOT_MODEL: str = "gemini-3.6-flash"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
