import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List

logger = logging.getLogger("crypto_analyzer.backtester")

class Backtester:
    """Module kiểm thử chiến lược giao dịch tự động trên dữ liệu lịch sử nến OHLCV (Backtesting Engine)."""

    def __init__(self, initial_capital: float = 10000.0, risk_per_trade_pct: float = 2.0):
        self.initial_capital = initial_capital
        self.risk_per_trade_pct = risk_per_trade_pct

    def run_backtest(self, df: pd.DataFrame, trailing_stop: bool = True) -> Dict[str, Any]:
        """Thực thi mô phỏng chiến lược trên dữ liệu lịch sử và tính toán các chỉ số hiệu suất."""
        if len(df) < 30:
            return {"error": "Dữ liệu nến quá ngắn để thực hiện backtest (Cần ít nhất 30 nến)"}

        df = df.copy()
        capital = self.initial_capital
        equity_curve = [capital]
        trades = []
        in_position = False
        position = None

        for i in range(25, len(df)):
            row = df.iloc[i]
            prev_row = df.iloc[i-1]

            close_p = float(row['close'])
            high_p = float(row['high'])
            low_p = float(row['low'])
            dt_str = str(row['datetime'])
            rsi = float(row['rsi_14'])
            sma20 = float(row['sma_20']) if not np.isnan(row['sma_20']) else close_p
            sma50 = float(row['sma_50']) if not np.isnan(row['sma_50']) else close_p
            atr = float(row['atr_14']) if not np.isnan(row['atr_14']) else close_p * 0.02

            # Nếu đang có vị thế -> Kiểm tra cắt lỗ / chốt lời
            if in_position and position:
                side = position['side']
                entry_price = position['entry_price']
                sl = position['stop_loss']
                tp = position['take_profit']
                amount = position['amount']

                # Cập nhật Trailing Stop nếu có tính năng
                if trailing_stop and side == "BUY":
                    if high_p > entry_price * 1.015:
                        # Dời SL lên mức hòa vốn hoặc theo ATR
                        new_sl = max(sl, entry_price * 1.002)
                        position['stop_loss'] = new_sl
                        sl = new_sl

                # Kiểm tra thoát lệnh BUY
                if side == "BUY":
                    if low_p <= sl:
                        exit_price = sl
                        pnl = (exit_price - entry_price) * amount
                        capital += (amount * exit_price)
                        trades.append({
                            "entry_time": position['entry_time'],
                            "exit_time": dt_str,
                            "side": "BUY",
                            "entry_price": round(entry_price, 2),
                            "exit_price": round(exit_price, 2),
                            "pnl_usdt": round(pnl, 2),
                            "pnl_pct": round((exit_price - entry_price) / entry_price * 100, 2),
                            "result": "LOSS" if pnl < 0 else "WIN",
                            "reason": "Stop Loss"
                        })
                        in_position = False
                        position = None
                    elif high_p >= tp:
                        exit_price = tp
                        pnl = (exit_price - entry_price) * amount
                        capital += (amount * exit_price)
                        trades.append({
                            "entry_time": position['entry_time'],
                            "exit_time": dt_str,
                            "side": "BUY",
                            "entry_price": round(entry_price, 2),
                            "exit_price": round(exit_price, 2),
                            "pnl_usdt": round(pnl, 2),
                            "pnl_pct": round((exit_price - entry_price) / entry_price * 100, 2),
                            "result": "WIN",
                            "reason": "Take Profit"
                        })
                        in_position = False
                        position = None

            # Nếu chưa có vị thế -> Kiểm tra tín hiệu Mua (Signal BUY)
            if not in_position:
                # Điều kiện Mua: RSI cắt lên từ vùng 40-55 + Giá > SMA20
                rsi_signal = rsi > 45 and prev_row['rsi_14'] <= 45
                ma_signal = close_p > sma20 and sma20 > sma50

                if rsi_signal and ma_signal:
                    risk_amount = capital * (self.risk_per_trade_pct / 100.0)
                    sl_dist = atr * 1.5
                    sl = close_p - sl_dist
                    tp = close_p + (sl_dist * 2.0)  # R:R = 1:2
                    amount = risk_amount / sl_dist if sl_dist > 0 else (capital * 0.1) / close_p
                    
                    cost = amount * close_p
                    if cost <= capital:
                        capital -= cost
                        position = {
                            "side": "BUY",
                            "entry_time": dt_str,
                            "entry_price": close_p,
                            "stop_loss": sl,
                            "take_profit": tp,
                            "amount": amount
                        }
                        in_position = True

            equity_curve.append(round(capital + (position['amount'] * close_p if in_position and position else 0.0), 2))

        # Tính toán các chỉ số định lượng
        total_trades = len(trades)
        winning_trades = [t for t in trades if t["result"] == "WIN"]
        losing_trades = [t for t in trades if t["result"] == "LOSS"]

        win_rate = (len(winning_trades) / total_trades * 100.0) if total_trades > 0 else 0.0
        final_capital = equity_curve[-1]
        total_return_pct = ((final_capital - self.initial_capital) / self.initial_capital) * 100.0

        gross_profit = sum(t["pnl_usdt"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl_usdt"] for t in losing_trades))
        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else (round(gross_profit, 2) if gross_profit > 0 else 1.0)

        # Tính Max Drawdown %
        equity_series = pd.Series(equity_curve)
        peak = equity_series.cummax()
        drawdown = (equity_series - peak) / peak
        max_drawdown_pct = round(abs(drawdown.min()) * 100.0, 2) if len(drawdown) > 0 else 0.0

        return {
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "total_return_pct": round(total_return_pct, 2),
            "win_rate_pct": round(win_rate, 2),
            "profit_factor": profit_factor,
            "max_drawdown_pct": max_drawdown_pct,
            "total_trades": total_trades,
            "winning_trades_count": len(winning_trades),
            "losing_trades_count": len(losing_trades),
            "trades_log": trades,
            "equity_curve": equity_curve
        }
