"""
AI陪伴学习系统 - 带认证的FastAPI Web服务器
包含用户注册、登录、摄像头集成和实时AI分析
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
import uvicorn
import json
from datetime import datetime, timedelta
import asyncio
import base64
import cv2
import numpy as np

# 导入核心系统
import sys
sys.path.append('.')
from main import AILearningCompanion
from storage.database import db, User
from auth import create_access_token, get_current_user, decode_access_token, TokenData
from ai_companion.doubao_api import doubao_client
from storage.auth_database import auth_db
from services.auth_service import (
    send_sms_code, login_with_phone, login_with_email,
    register_with_email, login_with_wechat_h5, login_with_wechat_mini,
    bind_phone, bind_email, unbind_auth, refresh_access_token,
    get_user_auth_accounts
)

# 创建FastAPI应用
app = FastAPI(
    title="AI陪伴学习系统",
    description="智能学习伙伴Web服务（带认证）",
    version="2.0.0"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局系统实例
companion_systems: Dict[int, AILearningCompanion] = {}  # user_id -> system
active_connections: Dict[int, WebSocket] = {}  # user_id -> websocket


# ==================== 数据模型 ====================

class UserRegister(BaseModel):
    """用户注册"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    user_type: str = "student"  # student, parent


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class VisionFrame(BaseModel):
    """视觉帧数据"""
    frame_data: str  # Base64编码的图像


class PhoneSMSRequest(BaseModel):
    """手机号发送验证码请求"""
    phone_number: str
    purpose: str = "login"  # login, register, bind


class PhoneLoginRequest(BaseModel):
    """手机号登录请求"""
    phone_number: str
    code: str
    device_id: Optional[str] = None


class EmailLoginRequest(BaseModel):
    """邮箱登录请求"""
    email: EmailStr
    password: str
    device_id: Optional[str] = None


class EmailRegisterRequest(BaseModel):
    """邮箱注册请求"""
    email: EmailStr
    password: str
    nickname: Optional[str] = None
    device_id: Optional[str] = None


class WeChatH5LoginRequest(BaseModel):
    """微信H5登录请求"""
    code: str  # OAuth code
    device_id: Optional[str] = None


class WeChatMiniLoginRequest(BaseModel):
    """微信小程序登录请求"""
    code: str  # 小程序登录code
    device_id: Optional[str] = None


class BindPhoneRequest(BaseModel):
    """绑定手机号请求"""
    phone_number: str
    code: str


class BindEmailRequest(BaseModel):
    """绑定邮箱请求"""
    email: EmailStr
    password: str


class UnbindRequest(BaseModel):
    """解绑认证请求"""
    auth_type: str  # phone, email, wechat_h5, wechat_mini


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


# ==================== 认证端点 ====================

@app.post("/api/auth/register")
async def register(user_data: UserRegister):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing_user = db.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 检查邮箱是否已存在
        existing_email = db.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(status_code=400, detail="邮箱已被注册")

        # 创建用户
        user = db.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            user_type=user_data.user_type
        )

        # 生成令牌
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            user_type=user.user_type
        )

        return {
            "success": True,
            "message": "注册成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "token": token
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login")
async def login(credentials: UserLogin):
    """用户登录"""
    try:
        # 验证用户
        user = db.authenticate_user(credentials.username, credentials.password)

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="账户已被禁用")

        # 生成令牌
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            user_type=user.user_type
        )

        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "user_id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "user_type": user.user_type,
                "token": token
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 多登录方式端点 ====================

@app.post("/api/auth/sms/send")
async def send_sms(request: PhoneSMSRequest):
    """发送短信验证码"""
    try:
        result = send_sms_code(request.phone_number, request.purpose)
        if result.get("success"):
            return {
                "success": True,
                "message": "验证码已发送",
                "data": {
                    "expires_in": 300  # 5分钟
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "发送失败"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login/phone")
async def login_phone(request: PhoneLoginRequest):
    """手机号+验证码登录"""
    try:
        result = login_with_phone(
            phone_number=request.phone_number,
            code=request.code,
            device_id=request.device_id
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "登录成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "登录失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login/email")
async def login_email(request: EmailLoginRequest):
    """邮箱+密码登录"""
    try:
        result = login_with_email(
            email=request.email,
            password=request.password,
            device_id=request.device_id
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "登录成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "登录失败"))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/register/email")
async def register_email(request: EmailRegisterRequest):
    """邮箱注册"""
    try:
        result = register_with_email(
            email=request.email,
            password=request.password,
            nickname=request.nickname,
            device_id=request.device_id
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "注册成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "注册失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login/wechat_h5")
async def login_wechat_h5(request: WeChatH5LoginRequest):
    """微信H5网页登录"""
    try:
        result = login_with_wechat_h5(
            code=request.code,
            device_id=request.device_id
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "登录成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "登录失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/login/wechat_mini")
async def login_wechat_mini(request: WeChatMiniLoginRequest):
    """微信小程序登录"""
    try:
        result = login_with_wechat_mini(
            code=request.code,
            device_id=request.device_id
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "登录成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "登录失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/token/refresh")
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        result = refresh_access_token(request.refresh_token)

        if result.get("success"):
            return {
                "success": True,
                "message": "令牌刷新成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=401, detail=result.get("error", "刷新失败"))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/bind/phone")
async def bind_phone_endpoint(
    request: BindPhoneRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """绑定手机号"""
    try:
        result = bind_phone(
            user_id=current_user.user_id,
            phone_number=request.phone_number,
            code=request.code
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "手机号绑定成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "绑定失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/bind/email")
async def bind_email_endpoint(
    request: BindEmailRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """绑定邮箱"""
    try:
        result = bind_email(
            user_id=current_user.user_id,
            email=request.email,
            password=request.password
        )

        if result.get("success"):
            return {
                "success": True,
                "message": "邮箱绑定成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "绑定失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/auth/unbind")
async def unbind_auth_endpoint(
    request: UnbindRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """解绑认证方式"""
    try:
        result = unbind_auth(
            user_id=current_user.user_id,
            auth_type=request.auth_type
        )

        if result.get("success"):
            return {
                "success": True,
                "message": f"已解绑{request.auth_type}",
                "data": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "解绑失败"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/accounts")
async def get_auth_accounts(current_user: TokenData = Depends(get_current_user)):
    """获取用户的所有认证账号"""
    try:
        accounts = get_user_auth_accounts(current_user.user_id)
        return {
            "success": True,
            "data": {
                "accounts": accounts
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """获取当前用户信息（包含会员状态和使用时长）"""
    user = db.get_user_by_username(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查使用限制
    can_use, remaining_time = db.check_usage_limit(user.id)

    # 获取今日使用记录
    today_usage = db.get_daily_usage(user.id)

    # 获取绑定的认证账号
    auth_accounts = get_user_auth_accounts(current_user.user_id)

    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "membership_type": user.membership_type,
            "is_vip": user.is_vip(),
            "membership_expires": user.membership_expires.isoformat() if user.membership_expires else None,
            "daily_limit": user.get_daily_limit(),
            "today_usage": today_usage.ai_analysis_time if today_usage else 0,
            "remaining_time": remaining_time,
            "can_use": can_use,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "linked_accounts": auth_accounts
        }
    }


# ==================== 学习会话端点 ====================

@app.post("/api/session/start")
async def start_session(current_user: TokenData = Depends(get_current_user)):
    """开始学习会话"""
    try:
        # 为用户创建系统实例
        if current_user.user_id not in companion_systems:
            companion_systems[current_user.user_id] = AILearningCompanion()

        system = companion_systems[current_user.user_id]
        session_info = system.start_session(f"user_{current_user.user_id}")

        # 保存会话记录到数据库
        db.create_session_record(
            user_id=current_user.user_id,
            session_id=session_info['session_id']
        )

        return {
            "success": True,
            "data": session_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/end")
async def end_session(current_user: TokenData = Depends(get_current_user)):
    """结束学习会话"""
    try:
        if current_user.user_id not in companion_systems:
            raise HTTPException(status_code=400, detail="没有活跃的学习会话")

        system = companion_systems[current_user.user_id]
        summary = system.end_session()

        # 更新数据库记录
        if summary:
            db.update_session_record(
                session_id=summary['session_id'],
                end_time=datetime.now(),
                total_time=summary.get('duration', 0),
                focused_time=summary.get('focused_time', 0),
                productivity_score=summary.get('productivity', 0),
                detected_topics=json.dumps(summary.get('topics_studied', []))
            )

        # 清理系统实例
        del companion_systems[current_user.user_id]

        return {
            "success": True,
            "data": summary
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 摄像头和AI分析端点 ====================

@app.post("/api/vision/analyze")
async def analyze_frame(
    frame: VisionFrame,
    current_user: TokenData = Depends(get_current_user)
):
    """分析摄像头帧（基础分析，不消耗AI时长）"""
    try:
        if current_user.user_id not in companion_systems:
            raise HTTPException(status_code=400, detail="请先开始学习会话")

        system = companion_systems[current_user.user_id]

        # 解码Base64图像
        img_data = base64.b64decode(frame.frame_data.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 处理帧（本地MediaPipe分析，不消耗AI配额）
        result = system.process_frame(img)

        # 如果有AI消息，通过WebSocket发送
        if result.get('ai_message') and current_user.user_id in active_connections:
            await active_connections[current_user.user_id].send_json({
                "type": "ai_intervention",
                "data": {
                    "message": result['ai_message'],
                    "timestamp": datetime.now().isoformat()
                }
            })

        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/vision/analyze_advanced")
async def analyze_frame_advanced(
    frame: VisionFrame,
    current_user: TokenData = Depends(get_current_user)
):
    """
    高级AI分析（使用豆包大模型）
    - 普通会员：每天30分钟
    - VIP会员：无限制
    """
    try:
        # 检查使用限制
        can_use, remaining_time = db.check_usage_limit(current_user.user_id)

        if not can_use:
            raise HTTPException(
                status_code=403,
                detail=f"今日AI分析时长已用完。剩余: 0秒。升级VIP可享受无限制使用！"
            )

        if current_user.user_id not in companion_systems:
            raise HTTPException(status_code=400, detail="请先开始学习会话")

        # 记录开始时间
        start_time = datetime.now()

        # 使用豆包API进行深度分析
        # 1. 分析学习内容
        content_result = doubao_client.analyze_learning_content(frame.frame_data)

        # 2. 分析姿势和状态
        state_result = doubao_client.analyze_posture_and_state(frame.frame_data)

        # 记录使用时间（假设每次分析消耗3秒）
        analysis_duration = 3
        allowed, new_remaining = db.add_usage_time(current_user.user_id, analysis_duration)

        # 获取用户信息
        user = db.get_user_by_id(current_user.user_id)

        return {
            "success": True,
            "data": {
                "learning_content": content_result,
                "posture_and_state": state_result,
                "usage_info": {
                    "is_vip": user.is_vip() if user else False,
                    "today_used": analysis_duration,
                    "remaining_time": new_remaining,
                    "can_continue": allowed
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI聊天端点 ====================

@app.post("/api/chat/message")
async def send_message(
    message: str,
    mode: str = "coach",
    current_user: TokenData = Depends(get_current_user)
):
    """向AI伙伴发送消息"""
    try:
        if current_user.user_id not in companion_systems:
            raise HTTPException(status_code=400, detail="请先开始学习会话")

        system = companion_systems[current_user.user_id]
        response = system.student_message(message, mode=mode)

        # 保存对话记录
        session = system.time_tracker.get_current_session(f"user_{current_user.user_id}")
        if session:
            db.save_ai_interaction(
                user_id=current_user.user_id,
                session_id=session.session_id,
                mode=mode,
                student_msg=message,
                ai_response=response.get('ai_message', ''),
                intent=response.get('intent', 'general')
            )

        return {
            "success": True,
            "data": response
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 仪表板端点 ====================

@app.get("/api/dashboard/student")
async def get_student_dashboard(current_user: TokenData = Depends(get_current_user)):
    """获取学生仪表板"""
    try:
        if current_user.user_id in companion_systems:
            system = companion_systems[current_user.user_id]
            dashboard = system.get_student_dashboard(f"user_{current_user.user_id}")
        else:
            # 从数据库加载历史数据
            dashboard = _load_dashboard_from_db(current_user.user_id)

        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/parent/{student_id}")
async def get_parent_dashboard(
    student_id: int,
    current_user: TokenData = Depends(get_current_user)
):
    """获取家长仪表板（需要家长权限）"""
    try:
        # TODO: 验证家长是否有权查看此学生的数据
        dashboard = _load_parent_dashboard_from_db(student_id)

        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _load_dashboard_from_db(user_id: int) -> Dict:
    """从数据库加载仪表板数据"""
    sessions = db.get_user_sessions(user_id, limit=30)
    knowledge = db.get_user_knowledge_map(user_id)

    # 计算统计数据
    total_time = sum(s.focused_time or 0 for s in sessions if s.focused_time)
    week_sessions = [s for s in sessions if s.start_time and
                    (datetime.now() - s.start_time).days < 7]
    week_time = sum(s.focused_time or 0 for s in week_sessions)

    # 计算连续天数
    streak = _calculate_streak(sessions)

    return {
        "today_minutes": 0,  # 需要从当天会话计算
        "week_minutes": week_time // 60,
        "month_minutes": total_time // 60,
        "streak": streak,
        "topics_mastered": len([k for k in knowledge if k.mastery_level >= 0.7]),
        "achievements": [],
        "productivity_trend": [],
        "recommendations": []
    }


def _calculate_streak(sessions: List) -> int:
    """计算连续学习天数"""
    if not sessions:
        return 0

    dates = set()
    for s in sessions:
        if s.start_time and s.focused_time and s.focused_time > 300:  # 至少5分钟
            dates.add(s.start_time.date())

    if not dates:
        return 0

    # 从今天开始倒数
    current_date = datetime.now().date()
    streak = 0

    while current_date in dates:
        streak += 1
        current_date = current_date - timedelta(days=1)

    return streak


def _load_parent_dashboard_from_db(student_id: int) -> Dict:
    """从数据库加载家长仪表板"""
    # 类似学生仪表板，但提供汇总数据
    sessions = db.get_user_sessions(student_id, limit=30)

    week_sessions = [s for s in sessions if s.start_time and
                    (datetime.now() - s.start_time).days < 7]

    week_time = sum(s.focused_time or 0 for s in week_sessions)
    total_time = sum(s.total_time or 0 for s in week_sessions)

    productivity = week_time / total_time if total_time > 0 else 0

    return {
        "week_total_time": week_time,
        "week_average_daily": week_time // 7,
        "month_total_time": sum(s.focused_time or 0 for s in sessions),
        "productivity_score": productivity,
        "consistency_score": 0.5,
        "engagement_level": "中等",
        "weekly_summary": f"本周学习了{week_time // 60}分钟",
        "subjects_progress": {},
        "recommendations_for_parent": ["继续鼓励孩子保持学习习惯"],
        "improvement_areas": [],
        "strengths": []
    }


# ==================== WebSocket端点 ====================

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket连接用于实时通信"""
    try:
        # 验证令牌
        user_data = decode_access_token(token)
        user_id = user_data.user_id

        await websocket.accept()
        active_connections[user_id] = websocket

        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": f"欢迎，{user_data.username}！",
            "user_id": user_id
        })

        # 持续监听消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            if message["type"] == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
        print(f"WebSocket断开: user_{user_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        if user_id in active_connections:
            del active_connections[user_id]


# ==================== 静态文件 ====================

@app.get("/", response_class=FileResponse)
async def index():
    """返回统一登录页面"""
    return FileResponse("../../frontend/public/login_unified.html")


@app.get("/login", response_class=FileResponse)
async def login_page():
    """登录页面（旧版兼容）"""
    return FileResponse("../../frontend/public/login.html")


@app.get("/student", response_class=FileResponse)
async def student_page():
    """学生学习页面"""
    return FileResponse("../../frontend/public/student.html")


@app.get("/parent", response_class=FileResponse)
async def parent_page():
    """家长仪表板页面"""
    return FileResponse("../../frontend/public/parent_auth.html")


@app.get("/account-settings", response_class=FileResponse)
async def account_settings_page():
    """账号设置页面"""
    return FileResponse("../../frontend/public/account_settings.html")


# ==================== 会员管理端点 ====================

class UpgradeRequest(BaseModel):
    """VIP升级请求"""
    days: int = 30  # VIP天数


@app.post("/api/membership/upgrade")
async def upgrade_to_vip(
    upgrade_req: UpgradeRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    升级为VIP会员
    注意：这是演示接口，实际应用需要集成支付系统
    """
    try:
        success = db.upgrade_to_vip(current_user.user_id, upgrade_req.days)

        if success:
            user = db.get_user_by_id(current_user.user_id)
            return {
                "success": True,
                "message": f"成功升级为VIP会员！有效期：{upgrade_req.days}天",
                "data": {
                    "membership_type": user.membership_type,
                    "membership_expires": user.membership_expires.isoformat() if user.membership_expires else None,
                    "daily_limit": user.get_daily_limit()
                }
            }
        else:
            raise HTTPException(status_code=500, detail="升级失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/membership/status")
async def get_membership_status(current_user: TokenData = Depends(get_current_user)):
    """获取会员状态"""
    try:
        user = db.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 获取使用统计
        can_use, remaining = db.check_usage_limit(current_user.user_id)
        today_usage = db.get_daily_usage(current_user.user_id)

        return {
            "success": True,
            "data": {
                "is_vip": user.is_vip(),
                "membership_type": user.membership_type,
                "membership_expires": user.membership_expires.isoformat() if user.membership_expires else None,
                "daily_limit": user.get_daily_limit(),
                "today_used": today_usage.ai_analysis_time if today_usage else 0,
                "remaining_time": remaining,
                "can_use_ai": can_use,
                "benefits": {
                    "free": ["每天30分钟AI分析", "基础学习跟踪", "AI伙伴对话"],
                    "vip": ["无限AI分析时长", "深度学习内容识别", "智能学习总结", "优先客服支持"]
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SummaryRequest(BaseModel):
    """学习总结请求"""
    session_id: Optional[str] = None


@app.post("/api/learning/generate_summary")
async def generate_learning_summary(
    summary_req: SummaryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    生成学习总结（使用豆包大模型）
    - 普通会员：消耗5秒AI时长
    - VIP会员：无限制
    """
    try:
        # 检查使用限制（生成总结消耗5秒）
        can_use, remaining_time = db.check_usage_limit(current_user.user_id)

        user = db.get_user_by_id(current_user.user_id)
        if not user.is_vip() and remaining_time < 5:
            raise HTTPException(
                status_code=403,
                detail="AI分析时长不足，无法生成总结。升级VIP可享受无限制使用！"
            )

        # 获取学习会话数据
        if current_user.user_id in companion_systems:
            system = companion_systems[current_user.user_id]
            session_data = system.get_session_summary()
        else:
            # 从数据库获取最近的会话
            sessions = db.get_user_sessions(current_user.user_id, limit=1)
            if not sessions:
                raise HTTPException(status_code=404, detail="没有找到学习会话")

            session = sessions[0]
            session_data = {
                "duration": (session.total_time or 0) // 60,
                "topics": json.loads(session.detected_topics) if session.detected_topics else [],
                "focus_level": (session.focused_time or 0) / max(session.total_time or 1, 1) * 100,
                "posture_scores": [75, 80, 85],  # 示例数据
                "detected_content": "学习内容"
            }

        # 使用豆包生成总结
        result = doubao_client.generate_learning_summary(session_data)

        if result.get("success"):
            # 记录使用时间
            if not user.is_vip():
                db.add_usage_time(current_user.user_id, 5)

            return {
                "success": True,
                "data": {
                    "summary": result["summary"],
                    "session_data": session_data
                }
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "生成总结失败"))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 系统端点 ====================

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "success": True,
        "data": {
            "status": "running",
            "version": "2.0.0",
            "active_sessions": len(companion_systems),
            "active_connections": len(active_connections),
            "features": {
                "basic_vision_analysis": True,
                "advanced_ai_analysis": True,
                "membership_system": True,
                "doubao_integration": True
            }
        }
    }


# ==================== 应用生命周期 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动"""
    print("=" * 60)
    print("🚀 AI陪伴学习系统 Web服务器启动（带认证）")
    print("=" * 60)
    print("📡 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔑 支持用户注册和登录")
    print("📹 支持摄像头实时分析")
    print("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    print("\n🛑 正在关闭系统...")
    for system in companion_systems.values():
        system.cleanup()
    print("✅ 系统已关闭")


# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server_auth:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
