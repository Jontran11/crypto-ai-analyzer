# Crypto AI Analyzer & Trading Bot Platform 🚀

Ứng dụng Web Phân tích và Dự đoán Giá Thị trường Tiền điện tử (tập trung vào BTC/USDT và Altcoins) theo mô hình **Đa phương pháp luận (Multi-Layer Financial Analysis)** kết hợp Phân tích Kỹ thuật (TA), Dòng tiền/On-Chain và Tâm lý Thị trường/Vĩ mô. Dự án tích hợp mô hình AI **Gemini 3.6 Flash** (`google-genai` SDK) với tham số tư duy định lượng (`thinking_level="medium"`), đồng thời cung cấp kiến trúc mở rộng sẵn sàng kết nối Module đặt lệnh tự động (**Exchange Executor & Trading Bot**).

---

## 📁 Cấu Trúc Dự Án (Project Structure)

```text
btc-ai-analyzer/
├── backend/
│   ├── __init__.py
│   ├── config.py           # Quản lý cấu hình, biến môi trường (GEMINI_API_KEY, host, port)
│   ├── data_fetcher.py     # Kết nối CCXT lấy dữ liệu nến OHLCV & tính toán chỉ báo TA (RSI, MA, MACD, BB, ATR)
│   ├── ai_analyzer.py      # Tích hợp Google GenAI SDK (Gemini 3.6 Flash) với Thinking Config & Structured Output Pydantic
│   ├── executor.py         # Module Exchange Executor & Bot đặt lệnh (hỗ trợ Paper Trading & Live Exchange)
│   └── main.py             # Server FastAPI chính định nghĩa các API Endpoints
│
├── frontend/
│   └── app.py              # Giao diện Web Streamlit Dashboard Dark Mode, Plotly Candlestick Chart, KPI Cards & Bot Controls
│
├── .env                    # Lưu trữ tham số cấu hình & API Keys
├── requirements.txt        # Danh sách thư viện phụ thuộc Python
└── README.md               # Tài liệu hướng dẫn chi tiết cài đặt và khởi chạy
```

---

## ⚙️ Yêu Cầu Tiền Trạm (Prerequisites)

- **Python**: Phiên bản 3.10 trở lên.
- **Gemini API Key**: Đăng ký tại [Google AI Studio](https://aistudio.google.com/) để lấy `GEMINI_API_KEY`.

---

## 🔐 Cấu Hình Môi Trường (.env)

Tạo hoặc chỉnh sửa file `.env` ở thư mục gốc của dự án với nội dung:

```env
# Google Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Định danh mô hình AI
GEMINI_MODEL=gemini-3.6-flash

# Cấu hình Backend Server
HOST=127.0.0.1
PORT=8000

# Thiết lập mặc định
DEFAULT_EXCHANGE=binance
DEFAULT_SYMBOL=BTC/USDT
DEFAULT_TIMEFRAME=1h
PAPER_TRADING=true
```

---

## 🖥️ Hướng Dẫn Khởi Chạy Chi Tiết Trên Terminal Windows

### Bước 1: Mở Terminal và di chuyển vào thư mục dự án

#### Trên Windows PowerShell:
```powershell
cd "C:\du-an\btc-ai-analyzer"
```

#### Trên Command Prompt (CMD):
```cmd
cd /d C:\du-an\btc-ai-analyzer
```

---

### Bước 2: Tạo và kích hoạt Môi trường ảo (Virtual Environment)

#### Trên PowerShell:
```powershell
# Tạo venv
python -m venv .venv

# Kích hoạt venv (nếu báo lỗi Execution Policy, chạy: Set-ExecutionPolicy Unrestricted -Scope Process)
.\.venv\Scripts\Activate.ps1

# Cập nhật pip và cài đặt thư viện
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Trên Command Prompt (CMD):
```cmd
:: Tạo venv
python -m venv .venv

:: Kích hoạt venv
.\.venv\Scripts\activate.bat

:: Cập nhật pip và cài đặt thư viện
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

### Bước 3: Khởi chạy Backend Server (FastAPI)

Mở cửa sổ Terminal thứ nhất (Backend Terminal) và chạy lệnh:

#### Trên PowerShell hoặc CMD:
```cmd
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
> 📌 Backend REST API sẽ lắng nghe tại: `http://127.0.0.1:8000`  
> 📌 Tài liệu Swagger UI tương tác: `http://127.0.0.1:8000/docs`

---

### Bước 4: Khởi chạy Frontend Dashboard (Streamlit)

Mở cửa sổ Terminal thứ hai (Frontend Terminal), kích hoạt `.venv` và chạy lệnh:

#### Trên PowerShell hoặc CMD:
```cmd
streamlit run frontend/app.py
```
> 📌 Giao diện Web Dashboard sẽ tự động mở tại trình duyệt: `http://localhost:8501`

---

## 🐧 Hướng Dẫn Khởi Chạy Trên macOS / Linux

```bash
# 1. Di chuyển tới thư mục dự án
cd "btc-ai-analyzer"

# 2. Tạo và kích hoạt môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# 3. Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# 4. Khởi chạy Backend (Terminal 1)
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 5. Khởi chạy Frontend (Terminal 2)
streamlit run frontend/app.py
```

---

## 📡 Danh Sách API Endpoints (Backend REST API)

- `GET /health`: Kiểm tra trạng thái hệ thống và cấu hình kết nối API.
- `GET /api/market-data`: Lấy nến OHLCV từ CCXT và chỉ báo kỹ thuật (RSI, MA, MACD, BB, ATR).
- `POST /api/analyze`: Gửi yêu cầu phân tích đa tầng tới Gemini 3.6 Flash AI Engine (`thinking_level="medium"`). Trả về JSON cấu trúc chuẩn Pydantic.
- `POST /api/execute-trade`: Đặt lệnh mua/bán tới Exchange Executor (Paper Trading hoặc Sàn live).
- `GET /api/balance`: Truy vấn số dư tài khoản mô phỏng/thực tế.

---

## 🤖 Định Hướng Phát Triển Giai Đoạn 2 (Exchange Executor & Trading Bot)

- Kết nối API Key / Secret Key của sàn giao dịch (Binance / Bybit / OKX via CCXT WebSocket & REST).
- Tích hợp chiến lược tự động đặt lệnh Limit/Stop-Market dựa trên `target_entry`, `stop_loss` và `take_profit` trả về từ AI Engine.
- Quản trị rủi ro vốn tự động (Capital Allocation % based on Risk/Reward Ratio).
