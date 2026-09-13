import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None

from backend.config import settings

logger = logging.getLogger("crypto_analyzer.ai_analyzer")

# Pydantic Schemas for Structured Output
class KeyArguments(BaseModel):
    technical_analysis: str = Field(
        description="Luận điểm phân tích kỹ thuật chi tiết dựa trên RSI, MACD, Moving Averages, Bollinger Bands và mô hình nến."
    )
    onchain_and_flows: str = Field(
        description="Luận điểm về dòng tiền thị trường, thanh khoản sàn giao dịch và các chỉ số On-chain liên quan."
    )
    market_sentiment: str = Field(
        description="Luận điểm về tâm lý thị trường (Fear & Greed Index), sự kiện vĩ mô và tin tức tác động."
    )

class TradingSignal(BaseModel):
    action: str = Field(description="Hành động giao dịch khuyến nghị cho bot: BUY, SELL, HOLD, WAIT")
    target_entry: Optional[float] = Field(None, description="Mức giá vào lệnh đề xuất (Entry Price)")
    stop_loss: Optional[float] = Field(None, description="Mức cắt lỗ đề xuất (Stop Loss)")
    take_profit_1: Optional[float] = Field(None, description="Mức chốt lời mục tiêu 1 (Take Profit 1)")
    take_profit_2: Optional[float] = Field(None, description="Mức chốt lời mục tiêu 2 (Take Profit 2)")
    position_size_pct: Optional[float] = Field(None, description="Tỷ lệ phần trăm vốn khuyến nghị (1-100%)")

class CryptoAnalysisResult(BaseModel):
    trend_short_term: str = Field(description="Xu hướng ngắn hạn: UP, DOWN, SIDEWAYS")
    support_levels: List[float] = Field(description="Các mức giá hỗ trợ chính (xếp theo thứ tự từ gần nhất đến xa nhất)")
    resistance_levels: List[float] = Field(description="Các mức giá kháng cự chính (xếp theo thứ tự từ gần nhất đến xa nhất)")
    risk_reward_ratio: float = Field(description="Tỷ lệ Rủi ro / Lợi nhuận (R:R ratio, ví dụ 2.5)")
    final_recommendation: str = Field(description="Khuyến nghị cuối cùng: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL")
    confidence_score: int = Field(description="Độ tin cậy của dự đoán trên thang điểm từ 1 đến 100")
    key_arguments: KeyArguments = Field(description="Luận điểm phân tích đa tầng chi tiết (TA, On-Chain/Flows, Sentiment)")
    trading_signal: TradingSignal = Field(description="Thông số lệnh giao dịch tự động cho bot exchange executor")

class AIAnalyzer:
    """Multi-layered Crypto Market Analysis Engine leveraging Google GenAI SDK (Gemini 3.6 Flash)."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL or "gemini-3.6-flash"

        if GENAI_AVAILABLE and self.api_key and self.api_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI Client: {e}")
                self.client = None
        else:
            self.client = None
            if not self.api_key or self.api_key == "your_gemini_api_key_here":
                logger.warning("GEMINI_API_KEY is not set or using placeholder. Running AIAnalyzer in simulation mode.")

    def analyze(self, market_summary: Dict[str, Any], macro_context: str = "") -> CryptoAnalysisResult:
        """Run deep multi-layered financial analysis on provided market summary using Gemini 3.6 Flash."""
        prompt = self._build_prompt(market_summary, macro_context)

        if self.client:
            try:
                # Configure thinking parameter level="medium" for financial reasoning as requested
                try:
                    thinking_cfg = types.ThinkingConfig(thinking_level="medium")
                except Exception:
                    # Fallback compatibility check for SDK variations
                    thinking_cfg = types.ThinkingConfig(thinking_budget=2048)

                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CryptoAnalysisResult,
                    thinking_config=thinking_cfg,
                    temperature=0.2,
                    system_instruction=(
                        "Bạn là một Kỹ sư Tài chính Định lượng và Chuyên gia Phân tích Crypto hàng đầu. "
                        "Nhiệm vụ của bạn là đánh giá dữ liệu thị trường và đưa ra dự đoán phân tích tài chính sâu sắc "
                        "kết hợp Phân tích kỹ thuật (TA), Dòng tiền/On-chain và Tâm lý thị trường/Vĩ mô. "
                        "Trả về dữ liệu JSON chính xác khớp tuyệt đối với schema Pydantic được yêu cầu."
                    )
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )

                if hasattr(response, 'parsed') and response.parsed:
                    return response.parsed
                elif response.text:
                    return CryptoAnalysisResult.model_validate_json(response.text)

            except Exception as e:
                logger.error(f"Error calling Gemini API: {e}. Falling back to rule-based fallback analysis.")

        return self._rule_based_fallback_analysis(market_summary, macro_context)

    def _build_prompt(self, market_summary: Dict[str, Any], macro_context: str) -> str:
        """Construct multi-layered prompt containing technical indicators, price action, and macro input."""
        symbol = market_summary.get("symbol", "BTC/USDT")
        price = market_summary.get("current_price", 0)
        timeframe = market_summary.get("timeframe", "1h")
        indicators = market_summary.get("indicators", {})

        prompt = f"""
Hãy tiến hành Phân tích Đa tầng (Multi-Layer Financial Analysis) cho cặp giao dịch {symbol} trên khung thời gian {timeframe}.

DỮ LIỆU THỊ TRƯỜNG HIỆN TẠI:
- Giá hiện tại: {price} USDT
- Biến động giai đoạn: {market_summary.get('price_change_period_pct', 0)}%
- Giá cao nhất period: {market_summary.get('high_24h', 0)} USDT
- Giá thấp nhất period: {market_summary.get('low_24h', 0)} USDT
- Khối lượng giao dịch: {market_summary.get('volume_latest', 0)}

CHỈ BÁO KỸ THUẬT:
- RSI (14): {indicators.get('rsi_14')}
- SMA 20: {indicators.get('sma_20')} | SMA 50: {indicators.get('sma_50')} | SMA 200: {indicators.get('sma_200')}
- EMA 9: {indicators.get('ema_9')} | EMA 21: {indicators.get('ema_21')}
- MACD: {indicators.get('macd')} | Signal: {indicators.get('macd_signal')} | Histogram: {indicators.get('macd_histogram')}
- Bollinger Bands: Upper={indicators.get('bb_upper')} | Mid={indicators.get('bb_middle')} | Lower={indicators.get('bb_lower')}
- ATR (14): {indicators.get('atr_14')}

BỐI CẢNH VĨ MÔ & TIN TỨC DO NGHƯỜI DÙNG CUNG CẤP:
{macro_context if macro_context.strip() else "Không có ghi chú vĩ mô bổ sung."}

YÊU CẦU ĐÁNH GIÁ:
1. Đánh giá Xu hướng Ngắn hạn (UP, DOWN, SIDEWAYS).
2. Xác định chính xác 2-3 mức Hỗ trợ (Support) và Kháng cự (Resistance) chính dựa trên dữ liệu giá và các chỉ báo.
3. Tính toán Tỷ lệ Rủi ro/Lợi nhuận (Risk/Reward Ratio) đề xuất cho lệnh.
4. Đưa ra Khuyến nghị Cuối cùng (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) kèm điểm tự tin (1-100).
5. Trình bày chi tiết 3 luận điểm:
   - technical_analysis: Phân tích sâu RSI, tín hiệu giao cắt MACD, nến và hỗ trợ/kháng cự.
   - onchain_and_flows: Đánh giá thanh khoản, áp lực mua/bán và dòng tiền.
   - market_sentiment: Đánh giá tác động của bối cảnh vĩ mô / tin tức tác động.
6. Thiết lập Tín hiệu Giao dịch chi tiết cho Bot: Target Entry, Stop Loss, Take Profit 1 & 2, và % vốn đề xuất.
"""
        return prompt

    def _rule_based_fallback_analysis(self, market_summary: Dict[str, Any], macro_context: str) -> CryptoAnalysisResult:
        """Deterministic rule-based fallback analysis engine when API is offline or key missing."""
        price = market_summary.get("current_price", 64000.0)
        indicators = market_summary.get("indicators", {})
        rsi = indicators.get("rsi_14", 50)
        sma20 = indicators.get("sma_20", price)
        sma50 = indicators.get("sma_50", price)
        atr = indicators.get("atr_14", price * 0.02)

        is_bullish = rsi > 50 and price > sma20
        is_bearish = rsi < 50 and price < sma20

        if is_bullish:
            trend = "UP"
            recommendation = "BUY" if rsi < 70 else "HOLD"
            action = "BUY"
            tp1 = round(price * 1.03, 2)
            tp2 = round(price * 1.06, 2)
            sl = round(price - (atr * 1.5), 2)
            entry = round(price, 2)
            confidence = 78
        elif is_bearish:
            trend = "DOWN"
            recommendation = "SELL" if rsi > 30 else "HOLD"
            action = "SELL"
            tp1 = round(price * 0.97, 2)
            tp2 = round(price * 0.94, 2)
            sl = round(price + (atr * 1.5), 2)
            entry = round(price, 2)
            confidence = 75
        else:
            trend = "SIDEWAYS"
            recommendation = "HOLD"
            action = "WAIT"
            tp1 = round(price * 1.02, 2)
            tp2 = round(price * 1.04, 2)
            sl = round(price * 0.98, 2)
            entry = round(price, 2)
            confidence = 65

        supp_1 = round(price - atr * 2, 2)
        supp_2 = round(price - atr * 4, 2)
        res_1 = round(price + atr * 2, 2)
        res_2 = round(price + atr * 4, 2)

        rr_ratio = round(abs(tp1 - entry) / max(abs(entry - sl), 1.0), 2)

        return CryptoAnalysisResult(
            trend_short_term=trend,
            support_levels=[supp_1, supp_2],
            resistance_levels=[res_1, res_2],
            risk_reward_ratio=rr_ratio,
            final_recommendation=recommendation,
            confidence_score=confidence,
            key_arguments=KeyArguments(
                technical_analysis=(
                    f"RSI đang ở mức {rsi:.1f}. Giá hiện tại ({price}) đang nằm "
                    f"{'trên' if price >= sma20 else 'dưới'} đường SMA20 ({sma20:.1f}). "
                    f"Biến động trung bình ATR khoảng {atr:.2f} USDT."
                ),
                onchain_and_flows=(
                    "Áp lực dòng tiền ghi nhận trạng thái cân bằng. "
                    "Khối lượng giao dịch duy trì ở mức ổn định xung quanh vùng giá hỗ trợ tĩnh."
                ),
                market_sentiment=(
                    f"Tâm lý thị trường chịu tác động bởi bối cảnh vĩ mô. Ghi nhận thông tin bổ sung: "
                    f"'{macro_context if macro_context else 'Không có tin tức vĩ mô đặc biệt'}'."
                )
            ),
            trading_signal=TradingSignal(
                action=action,
                target_entry=entry,
                stop_loss=sl,
                take_profit_1=tp1,
                take_profit_2=tp2,
                position_size_pct=15.0 if recommendation in ["BUY", "SELL"] else 5.0
            )
        )
