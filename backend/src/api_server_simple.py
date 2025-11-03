"""
AI陪伴学习系统 - 简化版Web服务器（用于快速测试）
只包含核心功能，不依赖复杂模块
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import uvicorn
from datetime import datetime, timedelta
import os
import hashlib
import secrets

# 创建FastAPI应用
app = FastAPI(
    title="AI陪伴学习系统（简化版）",
    description="用于测试的简化版服务器",
    version="2.0.0-simple"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/styles", StaticFiles(directory="../../frontend/public/styles"), name="styles")
app.mount("/js", StaticFiles(directory="../../frontend/public/js"), name="js")
app.mount("/assets", StaticFiles(directory="../../frontend/public/assets"), name="assets")

# 简单的内存用户存储（仅用于测试）
MOCK_USERS = {
    "test@example.com": {
        "user_id": 1,
        "email": "test@example.com",
        "password": "password123",  # 实际应用应该加密
        "username": "testuser",
        "full_name": "测试用户",
        "user_type": "student",
        "is_vip": False
    },
    "13800138000": {
        "user_id": 2,
        "phone": "13800138000",
        "username": "phoneuser",
        "full_name": "手机用户",
        "user_type": "student",
        "is_vip": False
    }
}

SECRET_KEY = "test-secret-key-change-in-production"

# ==================== 数据模型 ====================

class PhoneSMSRequest(BaseModel):
    phone_number: str
    purpose: str = "login"

class PhoneLoginRequest(BaseModel):
    phone_number: str
    code: str
    device_id: Optional[str] = None

class EmailLoginRequest(BaseModel):
    email: str
    password: str
    device_id: Optional[str] = None

# ==================== 辅助函数 ====================

def create_token(user_id: int, username: str) -> str:
    """创建简单token（不使用JWT，仅用于测试）"""
    # 生成随机token
    random_part = secrets.token_urlsafe(32)
    # 添加用户信息的哈希
    user_hash = hashlib.sha256(f"{user_id}:{username}:{SECRET_KEY}".encode()).hexdigest()[:16]
    return f"{random_part}.{user_hash}.{user_id}"

# ==================== 认证端点 ====================

@app.post("/api/auth/sms/send")
async def send_sms(request: PhoneSMSRequest):
    """发送短信验证码（模拟）"""
    return {
        "success": True,
        "message": "验证码已发送（模拟）",
        "data": {
            "expires_in": 300,
            "code": "123456"  # 仅用于测试
        }
    }

@app.post("/api/auth/login/phone")
async def login_phone(request: PhoneLoginRequest):
    """手机号+验证码登录（模拟）"""
    # 模拟验证码验证（测试时固定为123456）
    if request.code != "123456":
        raise HTTPException(status_code=401, detail="验证码错误")

    # 获取或创建用户
    if request.phone_number in MOCK_USERS:
        user = MOCK_USERS[request.phone_number]
    else:
        # 自动注册
        user = {
            "user_id": len(MOCK_USERS) + 1,
            "phone": request.phone_number,
            "username": f"user_{request.phone_number[-4:]}",
            "full_name": f"用户{request.phone_number[-4:]}",
            "user_type": "student",
            "is_vip": False
        }
        MOCK_USERS[request.phone_number] = user

    token = create_token(user["user_id"], user["username"])

    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "user": user,
            "token": token,
            "tokens": {
                "access_token": token,
                "refresh_token": token  # 简化版使用相同的token
            }
        }
    }

@app.post("/api/auth/login/email")
async def login_email(request: EmailLoginRequest):
    """邮箱+密码登录（模拟）"""
    if request.email not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="邮箱未注册")

    user = MOCK_USERS[request.email]
    if user.get("password") != request.password:
        raise HTTPException(status_code=401, detail="密码错误")

    token = create_token(user["user_id"], user["username"])

    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "user": user,
            "token": token,
            "tokens": {
                "access_token": token,
                "refresh_token": token
            }
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info():
    """获取当前用户信息（模拟）"""
    return {
        "success": True,
        "data": {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "测试用户",
            "user_type": "student",
            "membership_type": "free",
            "is_vip": False,
            "daily_limit": 1800,
            "today_usage": 0,
            "remaining_time": 1800,
            "can_use": True,
            "linked_accounts": []
        }
    }

@app.get("/api/auth/security-status")
async def get_security_status():
    """获取安全状态（模拟）"""
    return {
        "success": True,
        "data": {
            "security_score": 65,
            "has_phone": True,
            "has_email": False,
            "has_wechat": False,
            "linked_accounts_count": 1,
            "recommendations": [
                "绑定邮箱以便找回密码",
                "建议至少绑定两种登录方式"
            ]
        }
    }

@app.get("/api/auth/accounts")
async def get_auth_accounts():
    """获取用户的所有认证账号（模拟）"""
    return {
        "success": True,
        "data": {
            "accounts": [
                {
                    "auth_type": "phone",
                    "identifier": "138****8000",
                    "is_verified": True,
                    "created_at": "2025-11-01T10:00:00"
                }
            ]
        }
    }

# ==================== 静态页面路由 ====================

@app.get("/", response_class=FileResponse)
async def index():
    """返回现代化登录页面"""
    return FileResponse("../../frontend/public/login_modern.html")

@app.get("/login", response_class=FileResponse)
async def login_page():
    """登录页面"""
    return FileResponse("../../frontend/public/login_modern.html")

@app.get("/dashboard", response_class=FileResponse)
async def dashboard_page():
    """统一导航仪表板"""
    return FileResponse("../../frontend/public/dashboard.html")

@app.get("/student", response_class=FileResponse)
async def student_page():
    """学生学习页面"""
    return FileResponse("../../frontend/public/student.html")

@app.get("/account-settings", response_class=FileResponse)
async def account_settings_page():
    """账号设置页面"""
    return FileResponse("../../frontend/public/account_settings_modern.html")

# ==================== 系统端点 ====================

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "success": True,
        "data": {
            "status": "running",
            "version": "2.0.0-simple",
            "mode": "test",
            "features": {
                "basic_auth": True,
                "phone_login": True,
                "email_login": True,
                "static_files": True
            }
        }
    }

# ==================== 应用生命周期 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动"""
    print("=" * 60)
    print("🚀 AI陪伴学习系统 简化版服务器启动")
    print("=" * 60)
    print("📡 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("⚠️  这是简化版服务器，仅用于测试网页加载")
    print("💡 测试账号:")
    print("   邮箱: test@example.com")
    print("   密码: password123")
    print("   手机: 13800138000")
    print("   验证码: 123456")
    print("=" * 60)

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    print("\n🛑 正在关闭系统...")
    print("✅ 系统已关闭")

# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
