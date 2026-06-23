#!/usr/bin/env bash
# 启动 AI 后端服务
cd "$(dirname "$0")/../ai_backend"

echo "=== 安装依赖 ==="
pip install -q fastapi uvicorn 2>/dev/null

echo "=== 启动 AI 推荐服务 ==="
echo "API: http://127.0.0.1:8000"
echo "文档: http://127.0.0.1:8000/docs"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
