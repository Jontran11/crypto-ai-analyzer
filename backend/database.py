import sqlite3
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("crypto_analyzer.database")

DB_PATH = Path(__file__).resolve().parent.parent / "crypto_analyzer.db"

class DatabaseManager:
    """Quản lý CSDL SQLite lưu trữ lịch sử phân tích AI và nhật ký đặt lệnh."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Khởi tạo bảng cơ sở dữ liệu nếu chưa tồn tại."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Bảng lưu lịch sử phân tích AI
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timeframe TEXT NOT NULL,
                        current_price REAL NOT NULL,
                        trend TEXT NOT NULL,
                        recommendation TEXT NOT NULL,
                        confidence_score INTEGER NOT NULL,
                        risk_reward_ratio REAL NOT NULL,
                        target_entry REAL,
                        stop_loss REAL,
                        take_profit_1 REAL,
                        take_profit_2 REAL,
                        full_result_json TEXT NOT NULL,
                        created_at REAL NOT NULL
                    )
                """)

                # Bảng lưu lịch sử thực thi lệnh
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trade_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        order_id TEXT UNIQUE NOT NULL,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        order_type TEXT NOT NULL,
                        amount REAL NOT NULL,
                        executed_price REAL NOT NULL,
                        stop_loss REAL,
                        take_profit REAL,
                        status TEXT NOT NULL,
                        paper_trading INTEGER NOT NULL,
                        message TEXT,
                        timestamp REAL NOT NULL
                    )
                """)
                conn.commit()
                logger.info("Cơ sở dữ liệu SQLite đã được khởi tạo thành công.")
        except Exception as e:
            logger.error(f"Lỗi khởi tạo CSDL SQLite: {e}")

    def save_analysis(self, symbol: str, timeframe: str, current_price: float, result_dict: Dict[str, Any]) -> int:
        """Lưu kết quả phân tích AI vào CSDL."""
        try:
            sig = result_dict.get("trading_signal", {})
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO analysis_history (
                        symbol, timeframe, current_price, trend, recommendation,
                        confidence_score, risk_reward_ratio, target_entry, stop_loss,
                        take_profit_1, take_profit_2, full_result_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    symbol,
                    timeframe,
                    current_price,
                    result_dict.get("trend_short_term", "SIDEWAYS"),
                    result_dict.get("final_recommendation", "HOLD"),
                    result_dict.get("confidence_score", 70),
                    result_dict.get("risk_reward_ratio", 2.0),
                    sig.get("target_entry"),
                    sig.get("stop_loss"),
                    sig.get("take_profit_1"),
                    sig.get("take_profit_2"),
                    json.dumps(result_dict, ensure_ascii=False),
                    time.time()
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Lỗi khi lưu phân tích AI vào CSDL: {e}")
            return -1

    def get_analysis_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lấy danh sách các lượt phân tích AI gần nhất."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM analysis_history ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    item["full_result"] = json.loads(item["full_result_json"])
                    results.append(item)
                return results
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn lịch sử phân tích: {e}")
            return []

    def save_trade(self, trade_dict: Dict[str, Any]) -> bool:
        """Lưu nhật ký thực thi lệnh vào CSDL."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trade_history (
                        order_id, symbol, side, order_type, amount, executed_price,
                        stop_loss, take_profit, status, paper_trading, message, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade_dict["order_id"],
                    trade_dict["symbol"],
                    trade_dict["side"],
                    trade_dict["order_type"],
                    trade_dict["amount"],
                    trade_dict["executed_price"],
                    trade_dict.get("stop_loss"),
                    trade_dict.get("take_profit"),
                    trade_dict["status"],
                    1 if trade_dict.get("paper_trading", True) else 0,
                    trade_dict.get("message", ""),
                    trade_dict.get("timestamp", time.time())
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Lỗi khi lưu nhật ký đặt lệnh: {e}")
            return False

    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Lấy nhật ký các lệnh đã thực thi gần đây."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM trade_history ORDER BY id DESC LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Lỗi khi truy vấn lịch sử đặt lệnh: {e}")
            return []

db_manager = DatabaseManager()
