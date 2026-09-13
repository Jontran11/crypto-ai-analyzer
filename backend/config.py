import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

class Settings:
    """Application configuration settings supporting .env, OS environment, and Streamlit Secrets."""

    @property
    def GEMINI_API_KEY(self) -> str:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                return str(st.secrets["GEMINI_API_KEY"]).strip()
        except Exception:
            pass
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def GEMINI_MODEL(self) -> str:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GEMINI_MODEL" in st.secrets:
                return str(st.secrets["GEMINI_MODEL"]).strip()
        except Exception:
            pass
        return os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "127.0.0.1")

    @property
    def PORT(self) -> int:
        return int(os.getenv("PORT", "8000"))

    @property
    def DEFAULT_EXCHANGE(self) -> str:
        return os.getenv("DEFAULT_EXCHANGE", "binance")

    @property
    def DEFAULT_SYMBOL(self) -> str:
        return os.getenv("DEFAULT_SYMBOL", "BTC/USDT")

    @property
    def DEFAULT_TIMEFRAME(self) -> str:
        return os.getenv("DEFAULT_TIMEFRAME", "1h")

    @property
    def PAPER_TRADING(self) -> bool:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "PAPER_TRADING" in st.secrets:
                return str(st.secrets["PAPER_TRADING"]).lower() == "true"
        except Exception:
            pass
        return os.getenv("PAPER_TRADING", "true").lower() == "true"

    @property
    def EXCHANGE_API_KEY(self) -> str:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "EXCHANGE_API_KEY" in st.secrets:
                return str(st.secrets["EXCHANGE_API_KEY"]).strip()
        except Exception:
            pass
        return os.getenv("EXCHANGE_API_KEY", "").strip()

    @property
    def EXCHANGE_SECRET_KEY(self) -> str:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "EXCHANGE_SECRET_KEY" in st.secrets:
                return str(st.secrets["EXCHANGE_SECRET_KEY"]).strip()
        except Exception:
            pass
        return os.getenv("EXCHANGE_SECRET_KEY", "").strip()

    @property
    def APP_PASSWORD(self) -> str:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
                return str(st.secrets["APP_PASSWORD"]).strip()
        except Exception:
            pass
        return os.getenv("APP_PASSWORD", "crypto2026").strip()

settings = Settings()
