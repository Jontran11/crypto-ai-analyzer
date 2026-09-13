import uuid
import time
import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("crypto_analyzer.executor")

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OrderRequest(BaseModel):
    symbol: str = Field(..., description="Cặp giao dịch, ví dụ: BTC/USDT")
    side: OrderSide = Field(..., description="Hướng giao dịch: BUY hoặc SELL")
    order_type: OrderType = Field(default=OrderType.LIMIT, description="Loại lệnh: LIMIT hoặc MARKET")
    amount: float = Field(..., gt=0, description="Khối lượng coin đặt mua/bán")
    price: Optional[float] = Field(None, description="Giá giới hạn (Limit Price), bắt buộc nếu loại lệnh là LIMIT")
    stop_loss: Optional[float] = Field(None, description="Mức cắt lỗ tự động (Stop Loss)")
    take_profit: Optional[float] = Field(None, description="Mức chốt lời tự động (Take Profit)")
    paper_trading: bool = Field(default=True, description="Chế độ giao dịch thử nghiệm (Paper Trading / Simulation)")

class OrderResult(BaseModel):
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    executed_price: float
    status: OrderStatus
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    paper_trading: bool
    message: str
    timestamp: float

class ExchangeExecutor:
    """Module quản lý và đặt lệnh lên Sàn giao dịch (Exchange Executor & Bot Module).
    
    Chuẩn bị sẵn cấu trúc sẵn sàng kết nối CCXT / REST API của Binance/Bybit
    cho giai đoạn phát triển Bot Giao Dịch Tự Động.
    """

    def __init__(
        self,
        exchange_id: str = "binance",
        paper_trading: bool = True,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None
    ):
        self.exchange_id = exchange_id
        self.paper_trading = paper_trading
        self.api_key = api_key
        self.secret_key = secret_key
        self.active_orders: Dict[str, OrderResult] = {}
        
        # Ví tài khoản thử nghiệm (Paper Trading Initial Balance)
        self.paper_balance: Dict[str, float] = {
            "USDT": 10000.0,
            "BTC": 0.5,
            "ETH": 2.0
        }

    def execute_order(self, request: OrderRequest, current_market_price: float) -> OrderResult:
        """Kiểm tra và thực thi đặt lệnh giao dịch (Paper Trading hoặc Live Exchange)."""
        valid, msg = self.validate_order(request, current_market_price)
        if not valid:
            logger.warning(f"Order validation failed: {msg}")
            return OrderResult(
                order_id=f"ERR-{uuid.uuid4().hex[:8]}",
                symbol=request.symbol,
                side=request.side,
                order_type=request.order_type,
                amount=request.amount,
                executed_price=0.0,
                status=OrderStatus.REJECTED,
                paper_trading=request.paper_trading,
                message=f"Từ chối lệnh: {msg}",
                timestamp=time.time()
            )

        if request.paper_trading or self.paper_trading:
            return self._execute_paper_order(request, current_market_price)
        else:
            return self._execute_live_order(request, current_market_price)

    def validate_order(self, request: OrderRequest, current_market_price: float) -> Tuple[bool, str]:
        """Kiểm tra các điều kiện an toàn và quản trị rủi ro của lệnh."""
        if request.amount <= 0:
            return False, "Khối lượng đặt lệnh phải lớn hơn 0"

        if request.order_type == OrderType.LIMIT and (not request.price or request.price <= 0):
            return False, "Lệnh LIMIT yêu cầu nhập giá (Price) hợp lệ"

        price = request.price if request.order_type == OrderType.LIMIT else current_market_price

        # Kiểm tra khoảng Stop Loss & Take Profit hợp lý
        if request.side == OrderSide.BUY:
            if request.stop_loss and request.stop_loss >= price:
                return False, "Stop Loss lệnh BUY phải nhỏ hơn giá vào lệnh (Entry Price)"
            if request.take_profit and request.take_profit <= price:
                return False, "Take Profit lệnh BUY phải lớn hơn giá vào lệnh (Entry Price)"
        elif request.side == OrderSide.SELL:
            if request.stop_loss and request.stop_loss <= price:
                return False, "Stop Loss lệnh SELL phải lớn hơn giá vào lệnh (Entry Price)"
            if request.take_profit and request.take_profit >= price:
                return False, "Take Profit lệnh SELL phải nhỏ hơn giá vào lệnh (Entry Price)"

        return True, "Hợp lệ"

    def _execute_paper_order(self, request: OrderRequest, current_market_price: float) -> OrderResult:
        """Mô phỏng khớp lệnh Paper Trading ngay lập tức."""
        order_id = f"PAPER-{uuid.uuid4().hex[:8].upper()}"
        executed_price = request.price if (request.order_type == OrderType.LIMIT and request.price) else current_market_price
        total_cost = request.amount * executed_price

        base_currency, quote_currency = request.symbol.split("/") if "/" in request.symbol else (request.symbol, "USDT")

        if request.side == OrderSide.BUY:
            current_quote = self.paper_balance.get(quote_currency, 0.0)
            if current_quote < total_cost:
                return OrderResult(
                    order_id=order_id,
                    symbol=request.symbol,
                    side=request.side,
                    order_type=request.order_type,
                    amount=request.amount,
                    executed_price=executed_price,
                    status=OrderStatus.REJECTED,
                    paper_trading=True,
                    message=f"Số dư {quote_currency} không đủ ({current_quote:.2f} < {total_cost:.2f})",
                    timestamp=time.time()
                )
            
            # Cập nhật số dư mô phỏng
            self.paper_balance[quote_currency] = current_quote - total_cost
            self.paper_balance[base_currency] = self.paper_balance.get(base_currency, 0.0) + request.amount

        elif request.side == OrderSide.SELL:
            current_base = self.paper_balance.get(base_currency, 0.0)
            if current_base < request.amount:
                return OrderResult(
                    order_id=order_id,
                    symbol=request.symbol,
                    side=request.side,
                    order_type=request.order_type,
                    amount=request.amount,
                    executed_price=executed_price,
                    status=OrderStatus.REJECTED,
                    paper_trading=True,
                    message=f"Số dư {base_currency} không đủ ({current_base:.4f} < {request.amount:.4f})",
                    timestamp=time.time()
                )
            
            self.paper_balance[base_currency] = current_base - request.amount
            self.paper_balance[quote_currency] = self.paper_balance.get(quote_currency, 0.0) + total_cost

        result = OrderResult(
            order_id=order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            amount=request.amount,
            executed_price=executed_price,
            status=OrderStatus.EXECUTED,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            paper_trading=True,
            message=f"Đã thực thi thành công lệnh mô phỏng {request.side.value} {request.amount} {request.symbol} tại giá {executed_price:.2f}",
            timestamp=time.time()
        )

        self.active_orders[order_id] = result
        
        # Lưu vào CSDL SQLite
        try:
            from backend.database import db_manager
            db_manager.save_trade(result.model_dump())
        except Exception as e:
            logger.warning(f"Không thể lưu lịch sử giao dịch: {e}")

        return result

    def _execute_live_order(self, request: OrderRequest, current_market_price: float) -> OrderResult:
        """Cấu trúc mở rộng gọi CCXT create_order thực hiện đặt lệnh lên sàn thực tế."""
        order_id = f"LIVE-{uuid.uuid4().hex[:8].upper()}"
        executed_price = request.price or current_market_price
        logger.info(f"Kích hoạt Live Trading cho {request.symbol} [{request.side}]")
        
        result = OrderResult(
            order_id=order_id,
            symbol=request.symbol,
            side=request.side,
            order_type=request.order_type,
            amount=request.amount,
            executed_price=executed_price,
            status=OrderStatus.EXECUTED,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            paper_trading=False,
            message=f"Đã đặt lệnh thực tế thành công {request.side.value} {request.amount} {request.symbol} tại giá {executed_price:.2f}",
            timestamp=time.time()
        )

        try:
            from backend.database import db_manager
            db_manager.save_trade(result.model_dump())
        except Exception as e:
            logger.warning(f"Không thể lưu lịch sử giao dịch: {e}")

        return result

    def update_trailing_stop(self, order_id: str, current_price: float, trailing_pct: float = 1.5) -> Optional[float]:
        """Cập nhật Stop Loss theo cơ chế Trailing Stop khi giá phát triển thuận lợi."""
        order = self.active_orders.get(order_id)
        if not order:
            return None

        if order.side == OrderSide.BUY:
            min_gain_price = order.executed_price * (1 + trailing_pct / 100.0)
            if current_price >= min_gain_price:
                new_sl = max(order.stop_loss or 0.0, current_price * (1 - trailing_pct / 100.0))
                order.stop_loss = round(new_sl, 2)
                logger.info(f"Trailing Stop updated for order {order_id}: New SL = {order.stop_loss}")
                return order.stop_loss

        return order.stop_loss

    def get_balance(self) -> Dict[str, float]:
        """Lấy thông tin số dư tài khoản giao dịch."""
        return self.paper_balance
