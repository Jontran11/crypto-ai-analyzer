#!/bin/bash
# Shell script khởi chạy Crypto AI Analyzer trên macOS (MacBook)

echo "=================================================="
echo "⚡ Crypto AI Analyzer & Trading Bot - macOS Launcher"
echo "=================================================="

# Di chuyển về thư mục dự án
CD_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$CD_PATH"

# 1. Tạo môi trường ảo nếu chưa có
if [ ! -d ".venv" ]; then
    echo "📦 Tạo môi trường ảo Python (.venv)..."
    python3 -m venv .venv
fi

# 2. Kích hoạt môi trường ảo
source .venv/bin/activate

# 3. Cài đặt / cập nhật các thư viện
echo "📥 Kiểm tra và cài đặt thư viện từ requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Thông báo và khởi chạy ứng dụng
echo ""
echo "🚀 Đang khởi động Backend REST API (port 8000)..."
echo "📌 Backend URL: http://127.0.0.1:8000"
echo "📌 Swagger Docs: http://127.0.0.1:8000/docs"
echo ""

# Chạy Backend ở background
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Chờ 2 giây cho Backend sẵn sàng
sleep 2

echo "🎨 Đang khởi động Frontend Streamlit Dashboard (port 8501)..."
echo "📌 Frontend URL: http://localhost:8501"
echo ""

# Chạy Streamlit
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
streamlit run frontend/app.py --server.headless=true

# Dọn dẹp tiến trình backend khi dừng Streamlit
kill $BACKEND_PID
