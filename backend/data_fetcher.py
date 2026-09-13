try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None

import pandas as pd
import numpy as np
import logging
import requests
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger("crypto_analyzer.data_fetcher")
logging.basicConfig(level=logging.INFO)

class DataFetcher:
    """Handles fetching live OHLCV data via CCXT and public REST APIs, calculating technical indicators."""

    def __init__(self, exchange_id: str = "binance"):
        self.exchange_id = exchange_id.lower()
        self.exchange = self._init_exchange(self.exchange_id)

    def _init_exchange(self, exchange_id: str) -> Optional[Any]:
        if not CCXT_AVAILABLE:
            logger.warning("CCXT library is not installed. DataFetcher will use direct public REST APIs.")
            return None
        try:
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({
                'enableRateLimit': True,
                'timeout': 10000,
            })
            return exchange
        except Exception as e:
            logger.warning(f"Exchange {exchange_id} initialization error: {e}, falling back to public REST APIs.")
            return None

    def fetch_ohlcv(
        self,
        symbol: str = "BTC/USDT",
        timeframe: str = "1h",
        limit: int = 100
    ) -> pd.DataFrame:
        """Fetch live OHLCV candlestick data from CCXT exchange or public REST APIs."""
        df = None

        # 1. Try direct public REST APIs first (fastest and most reliable across cloud platforms)
        df = self._fetch_from_public_api(symbol=symbol, timeframe=timeframe, limit=limit)

        # 2. Try CCXT exchange connection if public API returned empty
        if (df is None or df.empty) and self.exchange:
            try:
                ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
                df = pd.DataFrame(
                    ohlcv,
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            except Exception as e:
                logger.warning(f"CCXT fetch_ohlcv error: {e}")

        # 3. Fallback to realistic market simulation if all network sources fail
        if df is None or df.empty:
            logger.error(f"Network APIs offline or blocked. Generating simulated market data for {symbol}.")
            df = self._generate_simulated_data(symbol=symbol, limit=limit)

        df = self.calculate_indicators(df)
        return df

    def _fetch_from_public_api(self, symbol: str = "BTC/USDT", timeframe: str = "1h", limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch live OHLCV data directly from Binance, Binance US, or Bybit public REST APIs."""
        clean_symbol = symbol.replace("/", "").upper()
        tf_map = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d"}
        interval = tf_map.get(timeframe, "1h")
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        # Source 1: Binance Global API
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={clean_symbol}&interval={interval}&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                rows = [
                    [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                    for k in data
                ]
                df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                logger.info(f"Successfully fetched LIVE {symbol} [{timeframe}] price: ${df.iloc[-1]['close']:,.2f} from Binance Global API.")
                return df
        except Exception as e:
            logger.warning(f"Binance Global API error: {e}")

        # Source 2: Binance US API
        try:
            url = f"https://api.binance.us/api/v3/klines?symbol={clean_symbol}&interval={interval}&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                rows = [
                    [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                    for k in data
                ]
                df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                logger.info(f"Successfully fetched LIVE {symbol} [{timeframe}] price: ${df.iloc[-1]['close']:,.2f} from Binance US API.")
                return df
        except Exception as e:
            logger.warning(f"Binance US API error: {e}")

        # Source 3: Bybit Public API
        try:
            bybit_tf = "15" if timeframe == "15m" else "60" if timeframe == "1h" else "240" if timeframe == "4h" else "D"
            url = f"https://api.bybit.com/v5/market/kline?category=spot&symbol={clean_symbol}&interval={bybit_tf}&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json().get("result", {}).get("list", [])
                rows = [
                    [int(k[0]), float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])]
                    for k in reversed(data)
                ]
                df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                logger.info(f"Successfully fetched LIVE {symbol} [{timeframe}] price: ${df.iloc[-1]['close']:,.2f} from Bybit Public API.")
                return df
        except Exception as e:
            logger.warning(f"Bybit Public API error: {e}")

        # Source 4: CryptoCompare Public API (Global Cloud Fallback)
        try:
            base_coin = symbol.split("/")[0].upper()
            quote_coin = symbol.split("/")[1].upper()
            url = f"https://min-api.cryptocompare.com/data/v2/histohour?fsym={base_coin}&tsym={quote_coin}&limit={limit}"
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json().get("Data", {}).get("Data", [])
                rows = [
                    [int(k['time']) * 1000, float(k['open']), float(k['high']), float(k['low']), float(k['close']), float(k['volumeto'])]
                    for k in data
                ]
                df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                logger.info(f"Successfully fetched LIVE {symbol} [{timeframe}] price: ${df.iloc[-1]['close']:,.2f} from CryptoCompare Public API.")
                return df
        except Exception as e:
            logger.warning(f"CryptoCompare Public API error: {e}")

        return None

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical analysis indicators (RSI, MA, EMA, MACD, Bollinger Bands, ATR)."""
        df = df.copy()

        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()

        # Exponential Moving Averages
        df['ema_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema_21'] = df['close'].ewm(span=21, adjust=False).mean()

        # Relative Strength Index (RSI - 14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        df['rsi_14'] = df['rsi_14'].fillna(50)

        # MACD (12, 26, 9)
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands (20, 2)
        std20 = df['close'].rolling(window=20).std()
        df['bb_middle'] = df['sma_20']
        df['bb_upper'] = df['bb_middle'] + (std20 * 2)
        df['bb_lower'] = df['bb_middle'] - (std20 * 2)

        # ATR (14) - Average True Range
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = tr.rolling(window=14).mean()

        return df

    def get_market_summary(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Summarize latest technical indicator values into a structured dict for AI input."""
        latest = df.iloc[-1]

        current_price = float(latest['close'])
        price_change_24h = float(((latest['close'] - df.iloc[0]['close']) / df.iloc[0]['close']) * 100)

        recent_candles = df.tail(10)[['datetime', 'open', 'high', 'low', 'close', 'volume', 'rsi_14', 'macd']].to_dict(orient='records')
        for c in recent_candles:
            c['datetime'] = str(c['datetime'])

        summary = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": round(current_price, 2),
            "price_change_period_pct": round(price_change_24h, 2),
            "high_24h": round(float(df['high'].max()), 2),
            "low_24h": round(float(df['low'].min()), 2),
            "volume_latest": round(float(latest['volume']), 2),
            "indicators": {
                "rsi_14": round(float(latest['rsi_14']), 2),
                "sma_20": round(float(latest['sma_20']), 2) if not np.isnan(latest['sma_20']) else current_price,
                "sma_50": round(float(latest['sma_50']), 2) if not np.isnan(latest['sma_50']) else current_price,
                "sma_200": round(float(latest['sma_200']), 2) if not np.isnan(latest['sma_200']) else current_price,
                "ema_9": round(float(latest['ema_9']), 2),
                "ema_21": round(float(latest['ema_21']), 2),
                "macd": round(float(latest['macd']), 4),
                "macd_signal": round(float(latest['macd_signal']), 4),
                "macd_histogram": round(float(latest['macd_hist']), 4),
                "bb_upper": round(float(latest['bb_upper']), 2) if not np.isnan(latest['bb_upper']) else current_price * 1.05,
                "bb_middle": round(float(latest['bb_middle']), 2) if not np.isnan(latest['bb_middle']) else current_price,
                "bb_lower": round(float(latest['bb_lower']), 2) if not np.isnan(latest['bb_lower']) else current_price * 0.95,
                "atr_14": round(float(latest['atr_14']), 2) if not np.isnan(latest['atr_14']) else current_price * 0.02
            },
            "recent_candles": recent_candles
        }

        return summary

    def _generate_simulated_data(self, symbol: str = "BTC/USDT", limit: int = 100) -> pd.DataFrame:
        """Generate realistic mock OHLCV data when exchange connection is unavailable."""
        base_price = 64000.0 if "BTC" in symbol else 3400.0 if "ETH" in symbol else 140.0
        now = pd.Timestamp.now()
        timestamps = [now - pd.Timedelta(hours=limit - i) for i in range(limit)]

        np.random.seed(42)
        returns = np.random.normal(loc=0.0002, scale=0.008, size=limit)
        prices = base_price * np.exp(np.cumsum(returns))

        data = []
        for i in range(limit):
            close = prices[i]
            open_p = prices[i-1] if i > 0 else close * 0.998
            high = max(open_p, close) * (1 + abs(np.random.normal(0, 0.003)))
            low = min(open_p, close) * (1 - abs(np.random.normal(0, 0.003)))
            volume = np.random.uniform(500, 3000)
            data.append([
                int(timestamps[i].timestamp() * 1000),
                round(open_p, 2),
                round(high, 2),
                round(low, 2),
                round(close, 2),
                round(volume, 2)
            ])

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
