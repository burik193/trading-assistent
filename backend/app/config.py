"""App config from environment."""
import os
from pydantic_settings import BaseSettings


def _dev_mode() -> bool:
    v = os.getenv("DEV_MODE", "").strip().lower()
    if v in ("1", "true", "yes"):
        return True
    return os.getenv("RUN_MODE", "").strip().lower() == "dev"


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_api_key_fallback: str = ""
    groq_model_fallback: str = "meta-llama/llama-guard-4-12b"
    database_url: str = "postgresql://user:password@localhost:5432/analyse_stocks"
    alpha_vantage_api_key: str = ""
    financial_news_api_key: str = ""  # Optional: e.g. NewsFilter.io for ticker-specific news
    dev_mode: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


def get_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_api_key_fallback=os.getenv("GROQ_API_KEY_FALLBACK", ""),
        groq_model_fallback=os.getenv("GROQ_MODEL_FALLBACK", "meta-llama/llama-guard-4-12b"),
        database_url=os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/analyse_stocks"),
        alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY", ""),
        financial_news_api_key=os.getenv("FINANCIAL_NEWS_API_KEY", ""),
        dev_mode=_dev_mode(),
    )
