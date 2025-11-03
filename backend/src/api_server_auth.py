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


@app.get("/api/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """获取当前用户信息"""
    user = db.get_user_by_username(current_user.username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "success": True,
        "data": {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
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
    """分析摄像头帧"""
    try:
        if current_user.user_id not in companion_systems:
            raise HTTPException(status_code=400, detail="请先开始学习会话")

        system = companion_systems[current_user.user_id]

        # 解码Base64图像
        img_data = base64.b64decode(frame.frame_data.split(',')[1])
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        # 处理帧
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
    """返回登录页面"""
    return FileResponse("../../frontend/public/login.html")


@app.get("/student", response_class=FileResponse)
async def student_page():
    """学生学习页面"""
    return FileResponse("../../frontend/public/student.html")


@app.get("/parent", response_class=FileResponse)
async def parent_page():
    """家长仪表板页面"""
    return FileResponse("../../frontend/public/parent_auth.html")


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
            "active_connections": len(active_connections)
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
