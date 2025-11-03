#!/bin/bash
# 快速启动脚本 - 简化版Web服务器

echo "=========================================="
echo "AI陪伴学习系统 - 快速启动脚本"
echo "=========================================="
echo ""

# 进入项目根目录
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "📁 项目目录: $PROJECT_ROOT"
echo ""

# 检查Python版本
echo "🐍 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"
echo ""

# 检查pip
echo "📦 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到pip3"
    exit 1
fi
echo "✅ pip已安装"
echo ""

# 安装最小化依赖
echo "📥 安装最小化依赖..."
echo "这可能需要几分钟时间..."
pip3 install -q fastapi uvicorn[standard] pydantic pyjwt passlib[bcrypt] sqlalchemy python-multipart requests

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "⚠️  部分依赖安装失败，但可能不影响基本功能"
fi
echo ""

# 检查目录结构
echo "📂 检查目录结构..."
if [ ! -d "frontend/public" ]; then
    echo "❌ 错误: frontend/public目录不存在"
    exit 1
fi

if [ ! -d "frontend/public/styles" ]; then
    echo "⚠️  警告: frontend/public/styles目录不存在，创建中..."
    mkdir -p frontend/public/styles
fi

if [ ! -d "frontend/public/js" ]; then
    echo "⚠️  警告: frontend/public/js目录不存在，创建中..."
    mkdir -p frontend/public/js
fi

if [ ! -d "frontend/public/assets" ]; then
    echo "⚠️  警告: frontend/public/assets目录不存在，创建中..."
    mkdir -p frontend/public/assets
fi

echo "✅ 目录结构正常"
echo ""

# 检查关键文件
echo "📄 检查关键文件..."
FILES_TO_CHECK=(
    "frontend/public/login_modern.html"
    "frontend/public/dashboard.html"
    "frontend/public/account_settings_modern.html"
    "frontend/public/student.html"
    "frontend/public/styles/design-system-enhanced.css"
    "backend/src/api_server_simple.py"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (缺失)"
    fi
done
echo ""

# 启动服务器
echo "=========================================="
echo "🚀 启动简化版Web服务器..."
echo "=========================================="
echo ""
echo "访问地址: http://localhost:8000"
echo "按 Ctrl+C 停止服务器"
echo ""

cd backend/src
python3 api_server_simple.py
