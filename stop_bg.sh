#!/bin/bash
# Shell script dừng các dịch vụ chạy ngầm của Crypto AI Analyzer

CD_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$CD_PATH"

echo "🛑 Đang dừng dịch vụ Crypto AI Analyzer ngầm..."

if [ -f "backend.pid" ]; then
    kill $(cat backend.pid) 2>/dev/null
    rm backend.pid
fi

if [ -f "frontend.pid" ]; then
    kill $(cat frontend.pid) 2>/dev/null
    rm frontend.pid
fi

pkill -f "uvicorn backend.main:app" 2>/dev/null
pkill -f "streamlit run frontend/app.py" 2>/dev/null

echo "✅ Đã dừng thành công toàn bộ ứng dụng."
