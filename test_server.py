#!/usr/bin/env python3
"""
测试脚本 - 检查服务器能否正常启动
"""

import sys
import os
import subprocess
import time

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """检查关键依赖"""
    print("\n📦 检查依赖...")
    required = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'jwt': 'PyJWT'
    }

    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✅ {name}")
        except ImportError:
            print(f"  ❌ {name} (未安装)")
            missing.append(name)

    if missing:
        print(f"\n⚠️  缺少依赖: {', '.join(missing)}")
        print("\n安装命令:")
        print("pip3 install fastapi uvicorn[standard] pydantic pyjwt")
        return False

    print("✅ 所有依赖已安装")
    return True

def check_files():
    """检查关键文件"""
    print("\n📄 检查文件...")
    files = {
        "frontend/public/login_modern.html": "登录页面",
        "frontend/public/dashboard.html": "主控台",
        "frontend/public/student.html": "学习页面",
        "frontend/public/account_settings_modern.html": "账号设置",
        "frontend/public/styles/design-system-enhanced.css": "样式文件",
        "backend/src/api_server_simple.py": "简化服务器"
    }

    all_exist = True
    for path, desc in files.items():
        if os.path.exists(path):
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc} ({path})")
            all_exist = False

    return all_exist

def check_directories():
    """检查目录结构"""
    print("\n📂 检查目录...")
    dirs = [
        "frontend/public/styles",
        "frontend/public/js",
        "frontend/public/assets"
    ]

    for d in dirs:
        if os.path.exists(d):
            print(f"  ✅ {d}")
        else:
            print(f"  ⚠️  {d} (不存在，将自动创建)")
            os.makedirs(d, exist_ok=True)

    return True

def test_import_server():
    """测试导入服务器模块"""
    print("\n🧪 测试服务器模块...")
    sys.path.insert(0, 'backend/src')

    try:
        # 测试基本导入
        from fastapi import FastAPI
        from uvicorn import run
        print("  ✅ 模块导入成功")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def main():
    print("=" * 60)
    print("AI陪伴学习系统 - 服务器测试")
    print("=" * 60)

    # 切换到项目根目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"\n📁 工作目录: {os.getcwd()}\n")

    # 运行检查
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("目录结构", check_directories),
        ("关键文件", check_files),
        ("模块导入", test_import_server)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name}检查失败: {e}")
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 60)
    print("检查汇总")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("\n🎉 所有检查通过！")
        print("\n启动服务器:")
        print("  方法1: bash start_simple.sh")
        print("  方法2: cd backend/src && python3 api_server_simple.py")
        print("\n访问地址: http://localhost:8000")
        return 0
    else:
        print("\n⚠️  部分检查失败，请先解决上述问题")
        return 1

if __name__ == "__main__":
    exit(main())
