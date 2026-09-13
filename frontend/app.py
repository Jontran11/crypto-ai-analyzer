import sys
from pathlib import Path
import streamlit as st
import plotly.graph_objects as pd_go
from plotly.subplots import make_subplots
import pandas as pd
import requests

# Add project root to sys.path for direct module import fallback
sys_path_root = str(Path(__file__).resolve().parent.parent)
if sys_path_root not in sys.path:
    sys.path.append(sys_path_root)

try:
    from backend.config import settings
    from backend.data_fetcher import DataFetcher
    from backend.ai_analyzer import AIAnalyzer
    from backend.executor import ExchangeExecutor, OrderRequest, OrderSide, OrderType
    BACKEND_MODULES_AVAILABLE = True
except ImportError:
    BACKEND_MODULES_AVAILABLE = False

import os

# Page Configuration
st.set_page_config(
    page_title="Crypto AI Analyzer - Trading Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Password Protection Gate
def check_password() -> bool:
    """Kiểm tra mật khẩu bảo vệ ứng dụng."""
    app_pwd = None
    try:
        if hasattr(st, "secrets") and "APP_PASSWORD" in st.secrets:
            app_pwd = st.secrets["APP_PASSWORD"]
    except Exception:
        pass
    if not app_pwd:
        app_pwd = os.getenv("APP_PASSWORD", "crypto2026")

    if st.session_state.get("password_correct", False):
        return True

    st.markdown("""
        <div style='text-align: center; padding: 40px;'>
            <h2>🔒 Crypto AI Analyzer & Trading Platform</h2>
            <p style='color: #848E9C;'>Ứng dụng được bảo vệ riêng tư. Vui lòng nhập mật khẩu để truy cập.</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("Nhập mật khẩu truy cập (Password):", type="password", key="pwd_input")
        if st.button("🔑 Đăng nhập / Truy cập Dashboard"):
            if user_input == app_pwd:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không chính xác. Vui lòng thử lại!")
    return False

if not check_password():
    st.stop()

# Custom Dark Theme CSS Styling
st.markdown("""
<style>
    /* Dark Theme Custom Adjustments */
    .main {
        background-color: #0E1117;
    }
    .stMetric {
        background-color: #1E222D;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #2A2E39;
    }
    .metric-card-positive {
        border-left: 5px solid #00E676 !important;
    }
    .metric-card-negative {
        border-left: 5px solid #FF5252 !important;
    }
    .metric-card-neutral {
        border-left: 5px solid #FFD600 !important;
    }
    .stButton>button {
        width: 100%;
        background-color: #2962FF;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        height: 48px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1E4BD8;
    }
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 15px;
        margin-bottom: 20px;
    }
    .kpi-box {
        background: #1E222D;
        border: 1px solid #2A2E39;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    .kpi-label {
        font-size: 13px;
        color: #848E9C;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: bold;
        color: #EAECEF;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to call backend API or direct module fallback
BACKEND_URL = "http://127.0.0.1:8000"

def fetch_data_from_backend(symbol: str, timeframe: str):
    """Fetch market data from API server or fallback to local backend module."""
    try:
        res = requests.get(f"{BACKEND_URL}/api/market-data", params={"symbol": symbol, "timeframe": timeframe}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data["candles"])
            summary = data["summary"]
            return df, summary
    except Exception:
        pass

    if BACKEND_MODULES_AVAILABLE:
        fetcher = DataFetcher()
        df = fetcher.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        summary = fetcher.get_market_summary(df, symbol=symbol, timeframe=timeframe)
        return df, summary
    
    st.error("Không thể kết nối với Backend Server và không tìm thấy module backend cục bộ.")
    st.stop()

def run_ai_analysis(symbol: str, timeframe: str, macro_context: str):
    """Trigger AI analysis from API server or fallback to local backend module."""
    try:
        res = requests.post(
            f"{BACKEND_URL}/api/analyze",
            json={"symbol": symbol, "timeframe": timeframe, "macro_context": macro_context},
            timeout=30
        )
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    if BACKEND_MODULES_AVAILABLE:
        fetcher = DataFetcher()
        analyzer = AIAnalyzer()
        df = fetcher.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=100)
        summary = fetcher.get_market_summary(df, symbol=symbol, timeframe=timeframe)
        result = analyzer.analyze(summary, macro_context=macro_context)
        return result.model_dump()

    return None

def execute_bot_trade(symbol: str, side: str, amount: float, price: float, sl: float, tp: float):
    """Send order request to backend executor."""
    order_data = {
        "symbol": symbol,
        "side": side,
        "order_type": "LIMIT",
        "amount": amount,
        "price": price,
        "stop_loss": sl,
        "take_profit": tp,
        "paper_trading": True
    }
    try:
        res = requests.post(f"{BACKEND_URL}/api/execute-trade", json=order_data, timeout=5)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    if BACKEND_MODULES_AVAILABLE:
        executor = ExchangeExecutor()
        req = OrderRequest(**order_data)
        res = executor.execute_order(req, current_market_price=price)
        return res.model_dump()

    return {"status": "REJECTED", "message": "Không kết nối được Exchange Executor"}

# Header Component
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("⚡ Crypto AI Analyzer & Trading Bot Platform")
    st.caption("Hệ thống Phân tích & Dự đoán Giá Thị trường Đa tầng kết hợp Gemini 3.6 Flash AI Engine")
with col_head2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.success("🟢 System Engine: Online")

st.divider()

# Sidebar Controls
st.sidebar.header("🔍 Cấu hình Phân tích")

symbol = st.sidebar.selectbox(
    "Cặp tiền giao dịch (Trading Pair):",
    options=["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"],
    index=0
)

timeframe = st.sidebar.select_slider(
    "Khung thời gian (Timeframe):",
    options=["15m", "1h", "4h", "1d"],
    value="1h"
)

st.sidebar.subheader("🌐 Bối cảnh Vĩ mô & On-Chain")
macro_input = st.sidebar.text_area(
    "Nhập sự kiện vĩ mô / tin tức tác động:",
    value="Fed giữ nguyên lãi suất. Chỉ số Fear & Greed đang ở mức 65. Dòng tiền chảy vào ETF BTC ghi nhận 200M USD.",
    height=120,
    help="Nhập thông tin tin tức, Fed, On-Chain hoặc dòng tiền để AI kết hợp phân tích đa tầng"
)

analyze_button = st.sidebar.button("🚀 Chạy Phân Tích AI Đa Tầng")

# Fetch Market Data
df_candles, summary_data = fetch_data_from_backend(symbol, timeframe)
current_price = summary_data["current_price"]
price_change = summary_data["price_change_period_pct"]
rsi_val = summary_data["indicators"]["rsi_14"]

# Top KPI Summary Bar
st.subheader(f"📊 Tổng quan Thị trường: {symbol} [{timeframe}]")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.metric(
        label="Giá hiện tại",
        value=f"${current_price:,.2f}",
        delta=f"{price_change:+.2f}%"
    )

with kpi2:
    st.metric(
        label="Chỉ báo RSI (14)",
        value=f"{rsi_val:.1f}",
        delta="Quá mua" if rsi_val > 70 else "Quá bán" if rsi_val < 30 else "Trung tính",
        delta_color="inverse" if rsi_val > 70 or rsi_val < 30 else "off"
    )

with kpi3:
    st.metric(
        label="Khối lượng (Volume)",
        value=f"{summary_data['volume_latest']:,.1f}"
    )

with kpi4:
    st.metric(
        label="SMA 20 / SMA 50",
        value=f"${summary_data['indicators']['sma_20']:,.0f}",
        delta=f"SMA50: ${summary_data['indicators']['sma_50']:,.0f}"
    )

with kpi5:
    st.metric(
        label="Dải Bollinger Trên/Dưới",
        value=f"${summary_data['indicators']['bb_upper']:,.0f}",
        delta=f"Dưới: ${summary_data['indicators']['bb_lower']:,.0f}"
    )

# Plotly Interactive Candlestick Chart
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    subplot_titles=(f'Biểu đồ nến kỹ thuật {symbol}', 'Khối lượng giao dịch & RSI'),
    row_width=[0.25, 0.75]
)

# Candlestick
fig.add_trace(
    pd_go.Candlestick(
        x=df_candles['datetime'],
        open=df_candles['open'],
        high=df_candles['high'],
        low=df_candles['low'],
        close=df_candles['close'],
        name='Nến OHLC'
    ),
    row=1, col=1
)

# Moving Averages Overlays
fig.add_trace(pd_go.Scatter(x=df_candles['datetime'], y=df_candles['sma_20'], line=dict(color='#FFD600', width=1.5), name='SMA 20'), row=1, col=1)
fig.add_trace(pd_go.Scatter(x=df_candles['datetime'], y=df_candles['sma_50'], line=dict(color='#2962FF', width=1.5), name='SMA 50'), row=1, col=1)
fig.add_trace(pd_go.Scatter(x=df_candles['datetime'], y=df_candles['bb_upper'], line=dict(color='#FF5252', width=1, dash='dot'), name='BB Upper'), row=1, col=1)
fig.add_trace(pd_go.Scatter(x=df_candles['datetime'], y=df_candles['bb_lower'], line=dict(color='#00E676', width=1, dash='dot'), name='BB Lower'), row=1, col=1)

# Volume Panel
colors = ['#00E676' if row['close'] >= row['open'] else '#FF5252' for _, row in df_candles.iterrows()]
fig.add_trace(pd_go.Bar(x=df_candles['datetime'], y=df_candles['volume'], marker_color=colors, name='Volume'), row=2, col=1)

fig.update_layout(
    template="plotly_dark",
    height=500,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# AI Multi-Layered Analysis Section
st.divider()
st.subheader("🤖 Kết quả Phân tích & Dự đoán từ Gemini 3.6 Flash Engine")

if analyze_button or "ai_analysis_result" in st.session_state:
    if analyze_button:
        with st.spinner("Đang kích hoạt Gemini 3.6 Flash với Tham số Tư duy Financial Reasoning (thinking_level=medium)..."):
            result_data = run_ai_analysis(symbol, timeframe, macro_input)
            st.session_state["ai_analysis_result"] = result_data

    ai_res = st.session_state.get("ai_analysis_result")
    
    if ai_res:
        # Recommendation Banner
        rec = ai_res.get("final_recommendation", "HOLD")
        trend = ai_res.get("trend_short_term", "SIDEWAYS")
        score = ai_res.get("confidence_score", 70)
        rr = ai_res.get("risk_reward_ratio", 2.0)
        
        banner_col1, banner_col2, banner_col3, banner_col4 = st.columns(4)
        with banner_col1:
            st.info(f"🚩 **Xu hướng Ngắn hạn:** `{trend}`")
        with banner_col2:
            st.success(f"🎯 **Khuyến nghị:** `{rec}`")
        with banner_col3:
            st.warning(f"⚖️ **Tỷ lệ R:R:** `{rr}`")
        with banner_col4:
            st.error(f"⭐ **Độ tin cậy:** `{score}/100`")

        # Multi-layer Analysis Tabs
        tab_ta, tab_flow, tab_macro, tab_signal = st.tabs([
            "📈 Luận điểm Phân tích Kỹ thuật",
            "💧 Dòng tiền & On-Chain",
            "🌐 Tâm lý & Vĩ mô",
            "🤖 Tín hiệu Bot Giao dịch"
        ])

        key_args = ai_res.get("key_arguments", {})

        with tab_ta:
            st.markdown(f"### 📈 Phân tích Kỹ thuật (Technical Analysis)")
            st.write(key_args.get("technical_analysis", "Chưa có dữ liệu."))
            
            c_supp, c_res = st.columns(2)
            with c_supp:
                st.markdown("**🛡️ Các mức giá Hỗ trợ (Support):**")
                for s_val in ai_res.get("support_levels", []):
                    st.code(f"${s_val:,.2f} USDT")
            with c_res:
                st.markdown("**🚧 Các mức giá Kháng cự (Resistance):**")
                for r_val in ai_res.get("resistance_levels", []):
                    st.code(f"${r_val:,.2f} USDT")

        with tab_flow:
            st.markdown(f"### 💧 Dòng tiền & Tín hiệu On-Chain")
            st.write(key_args.get("onchain_and_flows", "Chưa có dữ liệu."))

        with tab_macro:
            st.markdown(f"### 🌐 Tâm lý Thị trường & Tin tức Vĩ mô")
            st.write(key_args.get("market_sentiment", "Chưa có dữ liệu."))

        with tab_signal:
            st.markdown(f"### 🤖 Tham số Đặt lệnh cho Exchange Executor")
            sig = ai_res.get("trading_signal", {})
            
            sig_col1, sig_col2, sig_col3, sig_col4 = st.columns(4)
            entry = sig.get("target_entry") or current_price
            sl = sig.get("stop_loss") or (current_price * 0.97)
            tp1 = sig.get("take_profit_1") or (current_price * 1.04)
            pos_size = sig.get("position_size_pct") or 10.0

            with sig_col1:
                st.metric("Hành động", sig.get("action", "BUY"))
            with sig_col2:
                st.metric("Giá Entry đề xuất", f"${entry:,.2f}")
            with sig_col3:
                st.metric("Stop Loss (Cắt lỗ)", f"${sl:,.2f}")
            with sig_col4:
                st.metric("Take Profit (Chốt lời)", f"${tp1:,.2f}")

            st.divider()
            st.markdown("#### ⚡ Đặt lệnh Mô phỏng (Paper Trade Order Execution)")
            
            trade_col1, trade_col2 = st.columns(2)
            with trade_col1:
                amount_to_trade = st.number_input("Khối lượng đặt (Amount):", value=0.01 if "BTC" in symbol else 0.1, step=0.01)
            with trade_col2:
                st.markdown("<br>", unsafe_allow_html=True)
                execute_btn = st.button("⚡ Đặt lệnh qua Exchange Executor (Paper Trade)")

            if execute_btn:
                trade_side = "BUY" if sig.get("action") in ["BUY", "STRONG_BUY"] else "SELL"
                exec_result = execute_bot_trade(
                    symbol=symbol,
                    side=trade_side,
                    amount=amount_to_trade,
                    price=entry,
                    sl=sl,
                    tp=tp1
                )
                if exec_result.get("status") == "EXECUTED":
                    st.success(f"✅ {exec_result.get('message')}")
                    st.json(exec_result)
                else:
                    st.warning(f"⚠️ {exec_result.get('message')}")

else:
    st.info("💡 Bấm vào nút **'🚀 Chạy Phân Tích AI Đa Tầng'** ở thanh bên (Sidebar) để kích hoạt Gemini 3.6 Flash AI Engine.")

# Backtesting & Historical Analysis Engine Section
st.divider()
st.subheader("📊 Backtesting Engine & Lịch sử Phân tích AI (SQLite)")

bt_tab1, bt_tab2 = st.tabs(["⚙️ Chạy Kiểm Thử Backtest", "📜 Lịch sử Dự đoán & Đặt lệnh"])

with bt_tab1:
    st.markdown("#### Mô phỏng hiệu suất chiến lược giao dịch tự động trên dữ liệu nến lịch sử")
    bt_col1, bt_col2, bt_col3 = st.columns(3)
    with bt_col1:
        bt_capital = st.number_input("Vốn giả định ban đầu ($):", value=10000.0, step=1000.0)
    with bt_col2:
        bt_risk = st.number_input("% Rủi ro mỗi lệnh (%):", value=2.0, step=0.5)
    with bt_col3:
        bt_candles = st.slider("Số lượng nến lịch sử:", min_value=50, max_value=500, value=200)

    run_bt_btn = st.button("📈 Chạy Kiểm Thử Backtest")
    
    if run_bt_btn:
        with st.spinner("Đang chạy Backtest chiến lược trên dữ liệu lịch sử..."):
            try:
                res = requests.post(
                    f"{BACKEND_URL}/api/backtest",
                    json={"symbol": symbol, "timeframe": timeframe, "initial_capital": bt_capital, "risk_per_trade_pct": bt_risk, "limit": bt_candles},
                    timeout=15
                ).json()
            except Exception:
                if BACKEND_MODULES_AVAILABLE:
                    from backend.backtester import Backtester
                    fetcher = DataFetcher()
                    df_bt = fetcher.fetch_ohlcv(symbol, timeframe, bt_candles)
                    bt_obj = Backtester(bt_capital, bt_risk)
                    res = bt_obj.run_backtest(df_bt)
                else:
                    res = None

            if res and "error" not in res:
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Tổng ROI (%)", f"{res['total_return_pct']:+.2f}%")
                with m2:
                    st.metric("Tỷ lệ thắng (Win Rate)", f"{res['win_rate_pct']:.1f}%")
                with m3:
                    st.metric("Profit Factor", f"{res['profit_factor']:.2f}")
                with m4:
                    st.metric("Max Drawdown", f"-{res['max_drawdown_pct']:.2f}%")

                st.markdown(f"**Tổng số lệnh thực thi:** `{res['total_trades']}` | **Thắng:** `{res['winning_trades_count']}` | **Thua:** `{res['losing_trades_count']}`")
                
                # Equity Curve Chart
                fig_eq = pd_go.Figure()
                fig_eq.add_trace(pd_go.Scatter(y=res['equity_curve'], mode='lines', line=dict(color='#00E676', width=2), name='Tài sản (USDT)'))
                fig_eq.update_layout(template="plotly_dark", title="Đồ thị Tài sản (Equity Curve)", height=300)
                st.plotly_chart(fig_eq, use_container_width=True)

                if res['trades_log']:
                    st.markdown("##### 📜 Nhật ký Chi tiết các Lệnh Backtest")
                    st.dataframe(pd.DataFrame(res['trades_log']))
            elif res and "error" in res:
                st.warning(res["error"])

with bt_tab2:
    st.markdown("#### Lịch sử các đợt Phân tích AI được lưu trữ trong CSDL SQLite")
    try:
        hist_res = requests.get(f"{BACKEND_URL}/api/history", timeout=5).json()
        analyses_list = hist_res.get("analyses", [])
        trades_list = hist_res.get("trades", [])

        if analyses_list:
            df_an = pd.DataFrame(analyses_list)[['id', 'symbol', 'timeframe', 'current_price', 'trend', 'recommendation', 'confidence_score', 'risk_reward_ratio']]
            st.markdown(f"**Tổng số lượt AI đã phân tích:** `{len(analyses_list)}`")
            st.dataframe(df_an, use_container_width=True)
        else:
            st.info("Chưa có lịch sử phân tích trong SQLite. Hãy bấm '🚀 Chạy Phân Tích AI Đa Tầng' ở thanh bên!")

        if trades_list:
            st.markdown("##### 📜 Nhật ký Lệnh Đã Thực Thi")
            st.dataframe(pd.DataFrame(trades_list), use_container_width=True)
    except Exception as e:
        st.caption("Không thể truy vấn CSDL lịch sử trực tiếp.")

