#!/bin/bash
# Shell script khởi chạy ngầm 24/7 trên macOS (Bạn có thể đóng Terminal thoải mái)

CD_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$CD_PATH"

# Kích hoạt venv
source .venv/bin/activate
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo "=================================================="
echo "⚡ Crypto AI Analyzer - Starting 24/7 Background Service"
echo "=================================================="

# 1. Khởi chạy Backend FastAPI ngầm
nohup uvicorn backend.main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
echo "🟢 Backend API đã chạy ngầm (PID: $(cat backend.pid)) -> Log: backend.log"

# 2. Khởi chạy Frontend Streamlit ngầm
nohup streamlit run frontend/app.py --server.headless=true --server.port 8501 > frontend.log 2>&1 &
echo $! > frontend.pid
echo "🟢 Frontend Dashboard đã chạy ngầm (PID: $(cat frontend.pid)) -> Log: frontend.log"

echo ""
echo "--------------------------------------------------"
echo "🎉 HOÀN TẤT! Ứng dụng đã hoạt động ngầm 24/7."
echo "👉 Bạn có thể ĐÓNG CỬA SỔ TERMINAL NÀY THOẢI MÁI."
echo "📌 Địa chỉ Web: http://localhost:8501"
echo "📌 Để TẮT ứng dụng ngầm khi cần, chạy lệnh: ./stop_bg.sh"
echo "--------------------------------------------------"
