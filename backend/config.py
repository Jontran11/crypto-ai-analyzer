import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

def safe_get_secret(key: str, default: str = "") -> str:
    """Safely get secret from Streamlit secrets or OS env without throwing FileNotFoundError or KeyError."""
    try:
        import streamlit as st
        try:
            val = st.secrets.get(key, None)
            if val is not None:
                return str(val).strip()
        except Exception:
            pass
    except Exception:
        pass
    return os.getenv(key, default).strip()

class Settings:
    """Application configuration settings supporting .env, OS environment, and Streamlit Secrets."""

    @property
    def GEMINI_API_KEY(self) -> str:
        return safe_get_secret("GEMINI_API_KEY", "")

    @property
    def GEMINI_MODEL(self) -> str:
        return safe_get_secret("GEMINI_MODEL", "gemini-3.6-flash")

    @property
    def HOST(self) -> str:
        return safe_get_secret("HOST", "127.0.0.1")

    @property
    def PORT(self) -> int:
        try:
            return int(safe_get_secret("PORT", "8000"))
        except Exception:
            return 8000

    @property
    def DEFAULT_EXCHANGE(self) -> str:
        return safe_get_secret("DEFAULT_EXCHANGE", "binance")

    @property
    def DEFAULT_SYMBOL(self) -> str:
        return safe_get_secret("DEFAULT_SYMBOL", "BTC/USDT")

    @property
    def DEFAULT_TIMEFRAME(self) -> str:
        return safe_get_secret("DEFAULT_TIMEFRAME", "1h")

    @property
    def PAPER_TRADING(self) -> bool:
        val = safe_get_secret("PAPER_TRADING", "true")
        return str(val).lower() == "true"

    @property
    def EXCHANGE_API_KEY(self) -> str:
        return safe_get_secret("EXCHANGE_API_KEY", "")

    @property
    def EXCHANGE_SECRET_KEY(self) -> str:
        return safe_get_secret("EXCHANGE_SECRET_KEY", "")

    @property
    def APP_PASSWORD(self) -> str:
        return safe_get_secret("APP_PASSWORD", "crypto2026")

settings = Settings()
