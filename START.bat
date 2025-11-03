@echo off
chcp 65001 >nul
title AI陪伴学习系统 - 一键启动

cls
echo ╔════════════════════════════════════════════════════════╗
echo ║                                                        ║
echo ║     🚀 AI陪伴学习系统 - 一键启动                       ║
echo ║                                                        ║
echo ╚════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"
set PROJECT_ROOT=%CD%

echo 📁 项目目录: %PROJECT_ROOT%
echo.

REM 检查Python
echo 🔍 检查Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python
    echo 请先安装Python 3.8或更高版本
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python已安装: %PYTHON_VERSION%
echo.

REM 打开引导页面
echo 🌐 正在打开启动引导页面...
set GUIDE_PAGE=%PROJECT_ROOT%\frontend\public\start.html

if exist "%GUIDE_PAGE%" (
    start "" "%GUIDE_PAGE%"
    echo ✅ 引导页面已在浏览器中打开
) else (
    echo ⚠️  引导页面文件不存在
)

echo.
echo ════════════════════════════════════════════════════════
echo.
echo 📋 请按照引导页面的3个步骤操作：
echo.
echo   步骤1️⃣  安装依赖包 (30秒)
echo   步骤2️⃣  启动服务器 (在新终端)
echo   步骤3️⃣  访问系统 (浏览器)
echo.
echo ════════════════════════════════════════════════════════
echo.

REM 询问是否安装依赖
set /p INSTALL="❓ 是否现在安装依赖包？(y/n) "
echo.

if /i "%INSTALL%"=="y" (
    echo.
    echo 📦 开始安装依赖...
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    pip install fastapi "uvicorn[standard]" pydantic

    if %errorlevel% equ 0 (
        echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        echo ✅ 依赖安装成功！
        echo.

        set /p START="❓ 是否现在启动服务器？(y/n) "
        echo.

        if /i "!START!"=="y" (
            echo.
            echo 🚀 正在启动服务器...
            echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            echo.
            echo ⚠️  重要提示：
            echo   • 服务器将在此终端运行
            echo   • 保持此窗口打开
            echo   • 按 Ctrl+C 可停止服务器
            echo.
            echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            echo.

            timeout /t 2 >nul
            cd backend\src
            python api_server_simple.py
        ) else (
            echo.
            echo 📝 手动启动服务器的命令：
            echo.
            echo   cd backend\src
            echo   python api_server_simple.py
            echo.
            pause
        )
    ) else (
        echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        echo ❌ 依赖安装失败
        echo.
        echo 请手动安装：
        echo   pip install fastapi "uvicorn[standard]" pydantic
        echo.
        pause
    )
) else (
    echo.
    echo 📝 请按照引导页面的步骤1手动安装依赖
    echo.
    echo   pip install fastapi "uvicorn[standard]" pydantic
    echo.
)

echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 🎓 测试账号：
echo   手机号: 13800138000  验证码: 123456
echo   邮箱: test@example.com  密码: password123
echo.
echo 🌐 访问地址: http://localhost:8000
echo 📖 完整文档: README_快速开始.md
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pause
