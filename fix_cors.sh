#!/bin/bash

echo "🔧 修复跨域问题 - 诊断和解决方案"
echo "======================================="
echo ""

# 1. 检查后端是否运行
echo "1️⃣ 检查后端服务..."
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "   ✅ 后端服务正常运行"
else
    echo "   ❌ 后端服务未运行或无法访问"
    echo "   💡 解决方案：启动后端"
    echo "      cd backend && source venv/bin/activate && python app.py"
    echo ""
    exit 1
fi

echo ""

# 2. 测试 CORS
echo "2️⃣ 测试 CORS 配置..."
CORS_TEST=$(curl -s -X OPTIONS http://localhost:8000/api/health \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    -I 2>&1)

if echo "$CORS_TEST" | grep -i "access-control-allow-origin" > /dev/null; then
    echo "   ✅ CORS 配置正常"
else
    echo "   ⚠️ CORS 配置可能有问题"
    echo "   💡 后端已更新 CORS 配置，请重启后端服务"
fi

echo ""

# 3. 检查前端配置
echo "3️⃣ 检查前端配置..."
if [ -f "frontend/.env" ]; then
    echo "   ✅ 前端 .env 文件存在"
    echo "   内容："
    cat frontend/.env | grep REACT_APP_API_URL
else
    echo "   ⚠️ 前端 .env 文件不存在"
    echo "   正在创建..."
    cat > frontend/.env << 'EOF'
REACT_APP_API_URL=http://localhost:8000
EOF
    echo "   ✅ 已创建 frontend/.env"
fi

echo ""

# 4. 提供解决方案
echo "======================================="
echo "🎯 解决方案："
echo ""
echo "方法 1：重启服务（推荐）"
echo "   1. 停止当前运行的前后端服务（Ctrl+C）"
echo "   2. 重新运行启动脚本："
echo "      ./start.sh"
echo ""
echo "方法 2：手动重启"
echo "   后端："
echo "      cd backend && source venv/bin/activate && python app.py"
echo "   前端（新终端）："
echo "      cd frontend && npm start"
echo ""
echo "方法 3：清除缓存"
echo "   如果问题仍然存在，清除浏览器缓存或使用无痕模式"
echo ""
echo "======================================="
echo ""
echo "✅ 已更新的配置："
echo "   - backend/app.py（CORS 配置已优化）"
echo "   - frontend/.env（API URL 已确认）"
echo ""
echo "请重启服务后再试！"

