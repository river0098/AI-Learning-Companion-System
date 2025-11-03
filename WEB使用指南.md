# 🌐 AI陪伴学习系统 - Web版使用指南

## 📋 目录
1. [快速开始](#快速开始)
2. [启动服务器](#启动服务器)
3. [学生端使用](#学生端使用)
4. [家长端使用](#家长端使用)
5. [API接口文档](#api接口文档)
6. [故障排除](#故障排除)

---

## 快速开始

### 前置要求

确保已安装：
- Python 3.10+
- 所有依赖包（见requirements.txt）

### 安装额外依赖

Web版需要额外安装FastAPI相关依赖：

```bash
pip install fastapi uvicorn websockets
```

---

## 启动服务器

### 方法1：直接运行

```bash
cd backend/src
python api_server.py
```

### 方法2：使用uvicorn

```bash
cd backend/src
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

### 启动成功提示

你应该看到类似输出：

```
============================================================
🚀 AI陪伴学习系统 Web服务器启动
============================================================
📡 访问地址: http://localhost:8000
📖 API文档: http://localhost:8000/docs
🔌 WebSocket: ws://localhost:8000/ws/{student_id}
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 学生端使用

### 访问地址

浏览器打开：`http://localhost:8000`

### 使用步骤

#### 1. 开始学习会话

![登录界面](学生登录界面示意)

- 输入学生ID（例如：`student_001`）
- 输入学生姓名（可选）
- 点击"开始学习会话"

#### 2. 选择AI伙伴模式

系统提供三种互动模式：

| 模式 | 图标 | 特点 | 适用场景 |
|------|------|------|----------|
| **导师模式** | 🎓 | 解释概念、提供提示 | 遇到难题时 |
| **教练模式** | 💪 | 激励、庆祝成就 | 需要动力时 |
| **朋友模式** | 🤗 | 情感支持、轻松聊天 | 感到疲惫时 |

点击对应按钮即可切换模式。

#### 3. 与AI伙伴对话

**示例对话：**

```
学生："我不理解这道二次方程题"

AI（导师模式）："让我帮你！这道题的关键是什么？
                 你试过因式分解吗？"

学生："试过了，但不知道怎么分解"

AI："好的，让我给你一个提示。看看系数，
      你能找到两个数，它们的积是常数项，
      和是一次项系数吗？"
```

**快捷回复：**

AI有时会提供快捷回复按钮，点击即可快速回复。

#### 4. 查看学习仪表板

右侧实时显示：

- **今日学习时间**：当前会话累计时间
- **本周学习时间**：本周总学习时长
- **连续打卡**：连续学习天数
- **掌握的主题**：已掌握的知识点数量
- **近期成就**：获得的成就徽章

#### 5. 结束会话

点击"结束会话"按钮，系统会：
- 保存本次学习数据
- 显示学习总结
- 更新掌握度

---

## 家长端使用

### 访问地址

浏览器打开：`http://localhost:8000/parent.html`

### 使用步骤

#### 1. 输入学生ID

输入孩子的学生ID，点击"查看报告"

#### 2. 查看学习概览

家长仪表板显示：

**本周统计卡片：**
- 本周学习时间
- 日均学习时间
- 生产力评分（0-100%）
- 参与度（高/中/低）

#### 3. 阅读AI洞察

AI生成的本周总结，例如：

> "本周，您的孩子学习了180分钟。他们在数学方面进步显著。
> 专注度和参与度保持良好水平。"

#### 4. 查看学科进度

直观的进度条显示各学科掌握度：

```
数学      ████████░░ 82%
物理      ██████░░░░ 65%
英语      ███████░░░ 71%
```

#### 5. 获取支持建议

系统会提供个性化建议：

- ✓ 孩子在数学方面表现优秀，可以适当增加难度
- ✓ 建议关注英语阅读理解能力
- ✓ 保持规律的学习时间，有助于养成习惯

### 隐私保护

🔒 **重要提示：**
- 家长端**不显示**实时监控画面
- 只显示**汇总数据**和**趋势分析**
- 尊重孩子的学习隐私
- 提供洞察而非监视

---

## API接口文档

### 自动生成的文档

访问 `http://localhost:8000/docs` 查看完整的Swagger API文档。

### 主要端点

#### 1. 会话管理

**开始会话**
```http
POST /api/session/start
Content-Type: application/json

{
  "student_id": "student_001",
  "student_name": "小明"
}
```

**结束会话**
```http
POST /api/session/end?student_id=student_001
```

#### 2. AI聊天

**发送消息**
```http
POST /api/chat/message
Content-Type: application/json

{
  "student_id": "student_001",
  "message": "我不理解这道题",
  "mode": "guide"
}
```

响应：
```json
{
  "success": true,
  "data": {
    "ai_message": "让我帮你！具体是哪里不理解？",
    "mode": "guide",
    "requires_response": false,
    "suggested_responses": []
  }
}
```

#### 3. 仪表板

**获取学生仪表板**
```http
GET /api/dashboard/student/student_001
```

**获取家长仪表板**
```http
GET /api/dashboard/parent/student_001
```

#### 4. 系统状态

**检查服务器状态**
```http
GET /api/status
```

响应：
```json
{
  "success": true,
  "data": {
    "status": "running",
    "version": "1.0.0",
    "active_sessions": 1,
    "current_student": "student_001"
  }
}
```

### WebSocket连接

**连接**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/student_001');

ws.onopen = () => {
    console.log('已连接');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};
```

**发送消息**
```javascript
ws.send(JSON.stringify({
    type: 'chat',
    message: '你好',
    mode: 'coach'
}));
```

---

## 故障排除

### 问题1：无法访问网页

**症状：** 浏览器显示"无法访问此网站"

**解决方案：**
1. 确认服务器正在运行
   ```bash
   # 检查进程
   ps aux | grep api_server
   ```

2. 检查端口是否被占用
   ```bash
   # Linux/Mac
   lsof -i :8000

   # Windows
   netstat -ano | findstr :8000
   ```

3. 尝试更换端口
   ```bash
   uvicorn api_server:app --port 8001
   ```

### 问题2：API返回500错误

**症状：** 控制台显示500 Internal Server Error

**解决方案：**
1. 查看服务器日志
   ```bash
   # 日志会显示详细错误信息
   ```

2. 检查依赖是否完整安装
   ```bash
   pip install -r requirements.txt
   ```

3. 确认所有模块路径正确
   ```python
   # 在api_server.py中检查导入路径
   ```

### 问题3：WebSocket连接失败

**症状：** 聊天功能无响应

**解决方案：**
1. 检查浏览器控制台是否有WebSocket错误

2. 确认防火墙没有阻止WebSocket连接

3. 尝试使用HTTP轮询替代（修改前端代码）

### 问题4：仪表板数据不更新

**症状：** 刷新后数据仍然为0

**解决方案：**
1. 确认会话已正确开始

2. 模拟一些学习活动
   ```python
   # 通过API发送消息或记录练习
   ```

3. 检查数据库连接（如果使用持久化）

### 问题5：ModuleNotFoundError

**症状：**
```
ModuleNotFoundError: No module named 'fastapi'
```

**解决方案：**
```bash
pip install fastapi uvicorn websockets
```

### 问题6：CORS错误

**症状：** 浏览器控制台显示CORS策略错误

**解决方案：**
已在`api_server.py`中配置CORS，如仍有问题：

```python
# 修改CORS设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 高级功能

### 1. 自定义AI个性

编辑 `config/settings.yaml`：

```yaml
ai_companion:
  personality: "playful"  # 活泼型
  default_mode: "friend"
```

### 2. 调整采样频率

```yaml
camera:
  sample_interval: 5  # 每5秒采样一次
```

### 3. 启用隐私模式

```yaml
privacy:
  save_raw_images: false  # 始终保持false
  data_retention_days: 30  # 数据保留天数
```

---

## 生产部署建议

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 使用Gunicorn

```bash
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 使用Docker

```bash
# 将在下一次更新中提供Dockerfile
```

---

## 获取帮助

- **GitHub Issues**: https://github.com/river0098/AI-Learning-Companion-System/issues
- **文档**: 查看README.md和ARCHITECTURE.md
- **API文档**: http://localhost:8000/docs

---

**享受智能学习陪伴！** 🎓✨
