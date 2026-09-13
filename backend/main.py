import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.config import settings
from backend.data_fetcher import DataFetcher
from backend.ai_analyzer import AIAnalyzer, CryptoAnalysisResult
from backend.executor import ExchangeExecutor, OrderRequest, OrderResult

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crypto_analyzer.main")

# Initialize FastAPI App
app = FastAPI(
    title="Crypto AI Analyzer API",
    description="Hệ thống Phân tích & Dự đoán Thị trường Crypto Đa tầng tích hợp Gemini 3.6 Flash & Exchange Executor",
    version="1.0.0"
)

# CORS Middleware Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Instance Initializations
data_fetcher = DataFetcher(exchange_id=settings.DEFAULT_EXCHANGE)
ai_analyzer = AIAnalyzer(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
executor = ExchangeExecutor(exchange_id=settings.DEFAULT_EXCHANGE, paper_trading=settings.PAPER_TRADING)

from backend.database import db_manager
from backend.backtester import Backtester

# Request Models
class AnalyzeRequest(BaseModel):
    symbol: str = Field(default="BTC/USDT", description="Cặp tiền điện tử cần phân tích, ví dụ: BTC/USDT")
    timeframe: str = Field(default="1h", description="Khung thời gian nến: 15m, 1h, 4h, 1d")
    macro_context: Optional[str] = Field(default="", description="Bối cảnh tin tức vĩ mô hoặc sự kiện On-chain bổ sung")

class BacktestRequest(BaseModel):
    symbol: str = Field(default="BTC/USDT", description="Cặp tiền giao dịch")
    timeframe: str = Field(default="1h", description="Khung thời gian nến")
    initial_capital: float = Field(default=10000.0, description="Vốn ban đầu (USDT)")
    risk_per_trade_pct: float = Field(default=2.0, description="% Rủi ro tối đa mỗi lệnh")
    limit: int = Field(default=200, ge=30, le=1000, description="Số nến nạp cho backtest")

@app.get("/", tags=["General"])
def read_root():
    return {
        "status": "online",
        "app": "Crypto AI Analyzer Engine",
        "version": "2.0.0",
        "model": settings.GEMINI_MODEL,
        "docs_url": "/docs"
    }

@app.get("/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "gemini_api_configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
        "default_exchange": settings.DEFAULT_EXCHANGE,
        "default_symbol": settings.DEFAULT_SYMBOL,
        "paper_trading_mode": settings.PAPER_TRADING
    }

@app.get("/api/market-data", tags=["Market Data"])
def get_market_data(
    symbol: str = Query(default="BTC/USDT", description="Cặp tiền giao dịch"),
    timeframe: str = Query(default="1h", description="Khung thời gian"),
    limit: int = Query(default=100, ge=10, le=500, description="Số lượng nến")
):
    """Lấy dữ liệu nến OHLCV và các chỉ báo kỹ thuật đã tính toán (RSI, MA, MACD, BB, ATR)."""
    try:
        df = data_fetcher.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        summary = data_fetcher.get_market_summary(df, symbol=symbol, timeframe=timeframe)
        
        candles = df[['timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volume',
                     'rsi_14', 'sma_20', 'sma_50', 'sma_200', 'ema_9', 'ema_21',
                     'bb_upper', 'bb_middle', 'bb_lower', 'macd', 'macd_signal', 'macd_hist']].to_dict(orient='records')
        
        for c in candles:
            c['datetime'] = str(c['datetime'])

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "summary": summary,
            "candles": candles
        }
    except Exception as e:
        logger.error(f"Error in get_market_data endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Không thể lấy dữ liệu thị trường: {str(e)}")

@app.post("/api/analyze", response_model=CryptoAnalysisResult, tags=["AI Analysis"])
def analyze_market(request: AnalyzeRequest):
    """Thực hiện Phân tích Đa tầng (Technical, On-Chain, Sentiment) thông qua Gemini 3.6 Flash AI Engine."""
    try:
        logger.info(f"Received analysis request for {request.symbol} [{request.timeframe}]")
        
        df = data_fetcher.fetch_ohlcv(symbol=request.symbol, timeframe=request.timeframe, limit=100)
        market_summary = data_fetcher.get_market_summary(df, symbol=request.symbol, timeframe=request.timeframe)
        
        result = ai_analyzer.analyze(market_summary, macro_context=request.macro_context or "")
        
        # Lưu kết quả phân tích vào SQLite
        try:
            res_dict = result.model_dump()
            db_manager.save_analysis(request.symbol, request.timeframe, market_summary["current_price"], res_dict)
        except Exception as err:
            logger.warning(f"Lỗi khi lưu CSDL phân tích AI: {err}")

        return result

    except Exception as e:
        logger.error(f"Error during AI analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống phân tích AI: {str(e)}")

@app.post("/api/execute-trade", response_model=OrderResult, tags=["Trading Bot Executor"])
def execute_trade(order_request: OrderRequest):
    """Đặt lệnh giao dịch qua Exchange Executor Module (Hỗ trợ Paper Trading & Live Bot)."""
    try:
        df = data_fetcher.fetch_ohlcv(symbol=order_request.symbol, timeframe="1m", limit=2)
        current_price = float(df.iloc[-1]['close'])
        
        result = executor.execute_order(order_request, current_market_price=current_price)
        return result
    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi thực thi lệnh: {str(e)}")

@app.get("/api/balance", tags=["Trading Bot Executor"])
def get_balance():
    """Lấy số dư tài khoản mô phỏng/thực tế từ Exchange Executor."""
    return {"balance": executor.get_balance()}

@app.get("/api/history", tags=["History & Analytics"])
def get_history(limit: int = Query(default=50, ge=1, le=200)):
    """Lấy lịch sử phân tích AI và nhật ký giao dịch từ SQLite."""
    analyses = db_manager.get_analysis_history(limit=limit)
    trades = db_manager.get_trade_history(limit=limit)
    return {
        "analysis_count": len(analyses),
        "trade_count": len(trades),
        "analyses": analyses,
        "trades": trades
    }

@app.post("/api/backtest", tags=["History & Analytics"])
def run_backtest(req: BacktestRequest):
    """Thực thi Backtest chiến lược định lượng trên dữ liệu lịch sử nến OHLCV."""
    try:
        df = data_fetcher.fetch_ohlcv(symbol=req.symbol, timeframe=req.timeframe, limit=req.limit)
        backtester = Backtester(initial_capital=req.initial_capital, risk_per_trade_pct=req.risk_per_trade_pct)
        result = backtester.run_backtest(df, trailing_stop=True)
        return result
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail=f"Lỗi thực thi Backtest: {str(e)}")
