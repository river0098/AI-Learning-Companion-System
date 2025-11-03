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
import random

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

# ==================== AI聊天端点（模拟） ====================

# 简单的AI响应模板
AI_RESPONSES = {
    "coach": [
        "加油！你正在做得很好，继续保持专注！💪",
        "很棒！记得每学习25分钟休息5分钟哦。",
        "注意力很集中，保持这个状态！要不要喝点水？",
        "你已经学习了一段时间了，做得真不错！",
        "继续加油！学习贵在坚持。",
    ],
    "tutor": [
        "有什么不懂的可以问我哦，我会尽力帮助你！📚",
        "学习要循序渐进，不要着急。",
        "遇到难题很正常，耐心思考就能解决。",
        "可以试着用自己的话总结一下刚才学的内容。",
        "理解概念比死记硬背更重要。",
    ],
    "friend": [
        "学习累了吗？休息一下也很重要哦！😊",
        "你今天的学习状态很不错呢！",
        "加油！我相信你可以的！",
        "记得劳逸结合，身体健康也很重要。",
        "一起努力，让学习变得更有趣！",
    ]
}

@app.post("/api/session/start")
async def start_session():
    """开始学习会话（模拟）"""
    return {
        "success": True,
        "data": {
            "session_id": f"session_{int(datetime.now().timestamp())}",
            "start_time": datetime.now().isoformat(),
            "message": "学习会话已开始，加油！"
        }
    }

@app.post("/api/session/end")
async def end_session():
    """结束学习会话（模拟）"""
    return {
        "success": True,
        "data": {
            "duration": 1800,  # 30分钟
            "focused_time": 1500,  # 25分钟
            "productivity": 83,
            "message": "本次学习会话已结束，辛苦了！"
        }
    }

@app.post("/api/chat/message")
async def send_chat_message(message: str, mode: str = "coach"):
    """AI聊天（模拟智能回复）"""
    # 根据消息内容生成智能回复
    message_lower = message.lower()

    # 简单的关键词匹配
    if any(word in message_lower for word in ["累", "tired", "休息"]):
        response = "看起来你有点累了，建议休息5-10分钟，喝点水放松一下。适当休息能提高学习效率！😊"
    elif any(word in message_lower for word in ["不会", "不懂", "难", "困难"]):
        response = "遇到困难很正常，这恰恰说明你在挑战自己！可以试试：\n1. 把问题拆分成小块\n2. 查找相关资料\n3. 做个简单的笔记\n慢慢来，你一定能搞懂的！💪"
    elif any(word in message_lower for word in ["加油", "努力", "继续"]):
        response = "太棒了！你的学习态度真好！继续保持这份热情，成功就在前方！加油加油！🎉"
    elif any(word in message_lower for word in ["谢谢", "thanks"]):
        response = "不客气！能帮到你我很开心。有任何问题随时问我哦！😊"
    elif any(word in message_lower for word in ["你好", "hello", "hi"]):
        response = f"你好！我是你的AI学习伙伴（{mode}模式）。我会在学习过程中陪伴和鼓励你。有什么需要帮助的吗？"
    else:
        # 根据模式随机选择响应
        responses = AI_RESPONSES.get(mode, AI_RESPONSES["coach"])
        response = random.choice(responses)

        # 添加一些上下文相关的回复
        if len(message) > 20:
            response += " 我看到你说了很多，说明你在认真思考，这很好！"

    return {
        "success": True,
        "data": {
            "ai_message": response,
            "mode": mode,
            "timestamp": datetime.now().isoformat(),
            "intent": "general"
        }
    }

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
                "static_files": True,
                "ai_chat": True
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
