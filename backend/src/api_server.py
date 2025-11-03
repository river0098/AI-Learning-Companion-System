"""
AI陪伴学习系统 - FastAPI Web服务器
提供REST API和WebSocket支持的Web界面
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import uvicorn
import json
from datetime import datetime
import asyncio

# 导入核心系统
import sys
sys.path.append('.')
from main import AILearningCompanion

# 创建FastAPI应用
app = FastAPI(
    title="AI陪伴学习系统",
    description="智能学习伙伴Web服务",
    version="1.0.0"
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
companion_system = AILearningCompanion()

# 活跃的WebSocket连接
active_connections: Dict[str, WebSocket] = {}


# ==================== 数据模型 ====================

class SessionStart(BaseModel):
    student_id: str
    student_name: Optional[str] = None


class ChatMessage(BaseModel):
    student_id: str
    message: str
    mode: Optional[str] = "coach"  # guide, coach, friend


class ExerciseResult(BaseModel):
    student_id: str
    concept_id: str
    correct: bool
    time_spent: int


# ==================== REST API端点 ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """返回主页"""
    return FileResponse("../../frontend/public/index.html")


@app.post("/api/session/start")
async def start_session(session: SessionStart):
    """开始学习会话"""
    try:
        result = companion_system.start_session(session.student_id)

        # 通知WebSocket客户端
        if session.student_id in active_connections:
            await active_connections[session.student_id].send_json({
                "type": "session_started",
                "data": result
            })

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/end")
async def end_session(student_id: str):
    """结束学习会话"""
    try:
        summary = companion_system.end_session()

        # 通知WebSocket客户端
        if student_id in active_connections:
            await active_connections[student_id].send_json({
                "type": "session_ended",
                "data": summary
            })

        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/message")
async def send_message(chat: ChatMessage):
    """向AI伙伴发送消息"""
    try:
        response = companion_system.student_message(
            chat.message,
            mode=chat.mode
        )

        # 通知WebSocket客户端
        if chat.student_id in active_connections:
            await active_connections[chat.student_id].send_json({
                "type": "ai_response",
                "data": response
            })

        return {
            "success": True,
            "data": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/exercise/record")
async def record_exercise(exercise: ExerciseResult):
    """记录练习结果"""
    try:
        result = companion_system.record_exercise_result(
            concept_id=exercise.concept_id,
            correct=exercise.correct,
            time_spent=exercise.time_spent
        )

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/student/{student_id}")
async def get_student_dashboard(student_id: str):
    """获取学生仪表板"""
    try:
        dashboard = companion_system.get_student_dashboard(student_id)

        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/parent/{student_id}")
async def get_parent_dashboard(student_id: str):
    """获取家长仪表板"""
    try:
        dashboard = companion_system.get_parent_dashboard(student_id)

        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "success": True,
        "data": {
            "status": "running",
            "version": "1.0.0",
            "active_sessions": len(active_connections),
            "current_student": companion_system.current_student
        }
    }


# ==================== WebSocket端点 ====================

@app.websocket("/ws/{student_id}")
async def websocket_endpoint(websocket: WebSocket, student_id: str):
    """WebSocket连接用于实时通信"""
    await websocket.accept()
    active_connections[student_id] = websocket

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "message": "已连接到AI陪伴学习系统",
            "student_id": student_id
        })

        # 持续监听消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            if message["type"] == "chat":
                response = companion_system.student_message(
                    message["message"],
                    mode=message.get("mode", "coach")
                )

                await websocket.send_json({
                    "type": "ai_response",
                    "data": response
                })

            elif message["type"] == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        if student_id in active_connections:
            del active_connections[student_id]
        print(f"WebSocket断开: {student_id}")

    except Exception as e:
        print(f"WebSocket错误: {e}")
        if student_id in active_connections:
            del active_connections[student_id]


# ==================== 后台任务 ====================

async def monitor_sessions():
    """后台监控会话，定期检查是否需要AI干预"""
    while True:
        try:
            # 这里可以添加定期检查逻辑
            # 比如检测学生状态，触发AI干预等
            await asyncio.sleep(30)  # 每30秒检查一次

            # 示例：向所有活跃连接发送心跳
            for student_id, ws in active_connections.items():
                try:
                    await ws.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    pass

        except Exception as e:
            print(f"监控任务错误: {e}")
            await asyncio.sleep(30)


@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    print("=" * 60)
    print("🚀 AI陪伴学习系统 Web服务器启动")
    print("=" * 60)
    print("📡 访问地址: http://localhost:8000")
    print("📖 API文档: http://localhost:8000/docs")
    print("🔌 WebSocket: ws://localhost:8000/ws/{student_id}")
    print("=" * 60)

    # 启动后台监控任务
    asyncio.create_task(monitor_sessions())


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    print("\n🛑 正在关闭系统...")
    companion_system.cleanup()
    print("✅ 系统已关闭")


# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
