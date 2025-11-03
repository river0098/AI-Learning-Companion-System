#!/bin/bash

# AI陪伴学习系统 - 一键启动脚本
# 这个脚本会打开引导网页，然后启动服务器

clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                        ║"
echo "║     🚀 AI陪伴学习系统 - 一键启动                       ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# 获取项目根目录
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

echo "📁 项目目录: $PROJECT_ROOT"
echo ""

# 检查Python
echo "🔍 检查Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi
echo "✅ Python已安装: $(python3 --version)"
echo ""

# 打开引导页面
echo "🌐 正在打开启动引导页面..."
GUIDE_PAGE="$PROJECT_ROOT/frontend/public/start.html"

if [ -f "$GUIDE_PAGE" ]; then
    # 根据操作系统选择打开方式
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open "file://$GUIDE_PAGE" 2>/dev/null &
        elif command -v firefox &> /dev/null; then
            firefox "file://$GUIDE_PAGE" 2>/dev/null &
        elif command -v google-chrome &> /dev/null; then
            google-chrome "file://$GUIDE_PAGE" 2>/dev/null &
        else
            echo "⚠️  无法自动打开浏览器"
            echo "请手动打开: file://$GUIDE_PAGE"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "file://$GUIDE_PAGE"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        # Windows (Git Bash / Cygwin)
        start "file://$GUIDE_PAGE"
    else
        echo "⚠️  无法自动打开浏览器"
        echo "请手动打开: file://$GUIDE_PAGE"
    fi

    echo "✅ 引导页面已在浏览器中打开"
else
    echo "⚠️  引导页面文件不存在: $GUIDE_PAGE"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo ""
echo "📋 请按照引导页面的3个步骤操作："
echo ""
echo "  步骤1️⃣  安装依赖包 (30秒)"
echo "  步骤2️⃣  启动服务器 (在新终端)"
echo "  步骤3️⃣  访问系统 (浏览器)"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# 询问是否立即安装依赖
read -p "❓ 是否现在安装依赖包？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📦 开始安装依赖..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    pip3 install fastapi "uvicorn[standard]" pydantic

    if [ $? -eq 0 ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ 依赖安装成功！"
        echo ""

        # 询问是否立即启动服务器
        read -p "❓ 是否现在启动服务器？(y/n) " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""
            echo "🚀 正在启动服务器..."
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo "⚠️  重要提示："
            echo "  • 服务器将在此终端运行"
            echo "  • 保持此窗口打开"
            echo "  • 按 Ctrl+C 可停止服务器"
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""

            sleep 2
            cd backend/src
            python3 api_server_simple.py
        else
            echo ""
            echo "📝 手动启动服务器的命令："
            echo ""
            echo "  cd backend/src"
            echo "  python3 api_server_simple.py"
            echo ""
        fi
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "❌ 依赖安装失败"
        echo ""
        echo "请手动安装："
        echo "  pip3 install fastapi \"uvicorn[standard]\" pydantic"
        echo ""
    fi
else
    echo ""
    echo "📝 请按照引导页面的步骤1手动安装依赖"
    echo ""
    echo "  pip3 install fastapi \"uvicorn[standard]\" pydantic"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎓 测试账号："
echo "  手机号: 13800138000  验证码: 123456"
echo "  邮箱: test@example.com  密码: password123"
echo ""
echo "🌐 访问地址: http://localhost:8000"
echo "📖 完整文档: README_快速开始.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
