import os
from pathlib import Path
from dotenv import load_dotenv

# Path to the .env file in the root project directory
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

class Settings:
    """Application configuration settings."""
    
    # AI Engine Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    
    # Backend Server Settings
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Exchange & Market Defaults
    DEFAULT_EXCHANGE: str = os.getenv("DEFAULT_EXCHANGE", "binance")
    DEFAULT_SYMBOL: str = os.getenv("DEFAULT_SYMBOL", "BTC/USDT")
    DEFAULT_TIMEFRAME: str = os.getenv("DEFAULT_TIMEFRAME", "1h")
    
    # Bot Trading & Exchange API Credentials
    PAPER_TRADING: bool = os.getenv("PAPER_TRADING", "true").lower() == "true"
    EXCHANGE_API_KEY: str = os.getenv("EXCHANGE_API_KEY", "")
    EXCHANGE_SECRET_KEY: str = os.getenv("EXCHANGE_SECRET_KEY", "")
    EXCHANGE_PASSWORD: str = os.getenv("EXCHANGE_PASSWORD", "")

settings = Settings()
