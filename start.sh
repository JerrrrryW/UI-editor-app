#!/bin/bash

# HTML 智能编辑器启动脚本

echo "🚀 启动 HTML 智能编辑器..."
echo ""

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，正在从模板创建..."
    cp .env.example .env
    echo "✅ 已创建 .env 文件，请编辑并填入您的 API 密钥"
    echo ""
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python 3，请先安装"
    exit 1
fi

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装"
    exit 1
fi

# 启动后端
echo "📦 启动后端服务..."
cd backend

# 检查后端依赖
if [ ! -d "venv" ]; then
    echo "   创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
if [ ! -f "venv/.deps_installed" ]; then
    echo "   安装后端依赖..."
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

# 启动 Flask
echo "   Flask 服务启动中（端口 5000）..."
python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

cd ..

# 等待后端启动
echo ""
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否运行
if ! curl -s http://localhost:8000/api/health > /dev/null; then
    echo "❌ 后端启动失败，请检查 backend.log"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ 后端服务已启动"
echo ""

# 启动前端
echo "📱 启动前端应用..."
cd frontend

# 检查前端 .env 文件
if [ ! -f ".env" ]; then
    cp .env.example .env
fi

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo "   安装前端依赖（首次运行可能需要几分钟）..."
    npm install
fi

# 启动 React
echo "   React 应用启动中（端口 3000）..."
BROWSER=none npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

cd ..

echo ""
echo "============================================"
echo "✅ 应用启动成功！"
echo ""
echo "🌐 后端 API: http://localhost:8000"
echo "🌐 前端应用: http://localhost:3000"
echo ""
echo "📋 日志文件:"
echo "   - 后端: backend.log"
echo "   - 前端: frontend.log"
echo ""
echo "🛑 停止应用: Ctrl+C 或运行以下命令"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "============================================"
echo ""

# 保存 PID 到文件
echo "$BACKEND_PID $FRONTEND_PID" > .pids

# 等待用户中断
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f .pids; echo '✅ 服务已停止'; exit 0" INT TERM

# 打开浏览器（macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    sleep 3
    open http://localhost:3000
fi

# 保持脚本运行
wait

