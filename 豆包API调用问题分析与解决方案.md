# 豆包大模型API调用问题分析与解决方案

**日期**: 2025-11-03
**问题**: 打开网页时不能正常调用豆包大模型API

---

## 📋 目录

1. [问题现象](#问题现象)
2. [根本原因分析](#根本原因分析)
3. [豆包API集成架构](#豆包api集成架构)
4. [解决方案](#解决方案)
5. [测试与验证](#测试与验证)
6. [常见错误处理](#常见错误处理)
7. [优化建议](#优化建议)

---

## 问题现象

### 用户反馈
> "为什么打开网页时不能正常调用豆包大模型API"

### 可能的症状
1. **前端调用失败** - 浏览器控制台显示API请求错误
2. **返回错误响应** - API返回401/403/500等错误
3. **超时无响应** - 请求长时间等待后超时
4. **功能不可用** - AI分析、学习总结等功能无法使用

---

## 根本原因分析

### 原因1: API密钥配置问题 ⚠️

**文件位置**: `backend/src/ai_companion/doubao_api.py:301`

```python
DEFAULT_API_KEY = "1cf58d28-bb11-4211-92c9-60001ee76343"
doubao_client = DoubaoAPI(DEFAULT_API_KEY)
```

**问题**:
- 使用的是硬编码的默认API密钥
- 该密钥可能已过期、失效或配额用完
- 没有使用环境变量，不够灵活

**影响**:
所有豆包API调用都会失败，返回401认证错误。

---

### 原因2: 前端未正确调用API ⚠️

**豆包API的使用场景**:

#### 场景1: 高级视觉分析（需要手动触发）
- **端点**: `POST /api/vision/analyze_advanced`
- **调用位置**: `frontend/public/student.html`
- **触发方式**: 用户需要在学习页面主动点击"AI分析"按钮

**问题**:
- 打开网页时**不会自动调用**豆包API
- 需要用户手动触发
- 如果页面没有提供"AI分析"按钮，用户无法使用此功能

#### 场景2: 学习总结生成
- **端点**: `POST /api/learning/generate_summary`
- **调用位置**: 目前**没有前端页面调用此API**
- **触发方式**: 需要手动实现

**问题**:
- 前端没有集成学习总结功能
- 用户无法生成学习报告

---

### 原因3: 网络连接问题 ⚠️

**豆包API地址**:
```python
self.base_url = "https://ark.cn-beijing.volces.com/api/v3"
```

**可能的问题**:
- 网络防火墙阻止外部API请求
- DNS解析失败
- SSL证书验证失败
- 超时设置太短（当前30秒）

---

### 原因4: 会员限制 ⚠️

**代码逻辑**: `api_server_auth.py:687-694`

```python
# 检查使用限制
can_use, remaining_time = db.check_usage_limit(current_user.user_id)

if not can_use:
    raise HTTPException(
        status_code=403,
        detail=f"今日AI分析时长已用完。剩余: 0秒。升级VIP可享受无限制使用！"
    )
```

**问题**:
- 普通用户每天只有30分钟（1800秒）AI分析时长
- 超过限制后无法调用豆包API
- 每次调用消耗3秒配额

**影响**:
- 普通用户每天最多调用600次（1800÷3）
- 超限后返回403错误

---

## 豆包API集成架构

### 系统架构

```
┌─────────────────┐
│  前端页面        │
│  student.html   │
│  (学习中心)      │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────────────────────────┐
│  FastAPI后端                         │
│  api_server_auth.py                 │
│                                      │
│  ┌───────────────────────────────┐  │
│  │ POST /api/vision/analyze      │  │
│  │ (基础分析，不调用豆包)         │  │
│  └───────────────────────────────┘  │
│                                      │
│  ┌───────────────────────────────┐  │
│  │ POST /api/vision/analyze_     │  │
│  │      advanced                  │  │
│  │ (高级分析，调用豆包)           │  │
│  │                                │  │
│  │ 1. 检查会员权限               │  │
│  │ 2. 调用豆包API                │  │
│  │ 3. 扣除使用时长               │  │
│  └────────┬──────────────────────┘  │
│           │                          │
│           ▼                          │
│  ┌───────────────────────────────┐  │
│  │ doubao_client                  │  │
│  │ (ai_companion/doubao_api.py) │  │
│  │                                │  │
│  │ • analyze_learning_content()  │  │
│  │ • analyze_posture_and_state() │  │
│  │ • generate_learning_summary() │  │
│  │ • chat()                       │  │
│  └────────┬──────────────────────┘  │
└───────────┼──────────────────────────┘
            │ HTTPS Request
            ▼
┌─────────────────────────────────────┐
│  豆包大模型API                       │
│  ark.cn-beijing.volces.com          │
│                                      │
│  • 视觉识别                          │
│  • 学习内容分析                      │
│  • 姿势状态分析                      │
│  • 智能总结生成                      │
└─────────────────────────────────────┘
```

---

### API调用流程

#### 流程1: 高级视觉分析

```
用户操作
  │
  ├─> 点击"开始学习"
  │     └─> 访问 /student 页面
  │
  ├─> 开启摄像头
  │     └─> 获取视频流
  │
  ├─> 点击"AI深度分析"按钮（需要实现）
  │     │
  │     ├─> 捕获当前帧
  │     │     └─> 转为Base64
  │     │
  │     ├─> 发送请求到 /api/vision/analyze_advanced
  │     │     │
  │     │     ├─> 后端检查会员权限
  │     │     │     ├─> 普通用户: 检查剩余时长
  │     │     │     └─> VIP用户: 无限制
  │     │     │
  │     │     ├─> 调用 doubao_client.analyze_learning_content()
  │     │     │     └─> 识别学习内容、学科、难度等
  │     │     │
  │     │     ├─> 调用 doubao_client.analyze_posture_and_state()
  │     │     │     └─> 分析坐姿、专注度、情绪
  │     │     │
  │     │     ├─> 扣除3秒使用时长
  │     │     │
  │     │     └─> 返回分析结果
  │     │
  │     └─> 前端显示分析结果
```

---

## 解决方案

### 解决方案1: 配置正确的API密钥 ✅

#### 步骤1: 获取豆包API密钥

1. 访问火山引擎控制台: https://console.volcengine.com/ark
2. 创建或登录账号
3. 进入"API密钥"管理
4. 创建新的API密钥或使用现有密钥
5. 复制API密钥（格式类似：`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

#### 步骤2: 使用环境变量配置

**方法1: 修改代码使用环境变量**

编辑 `backend/src/ai_companion/doubao_api.py`:

```python
import os

# 修改第299-302行
# 从环境变量读取API密钥，如果不存在则使用默认值
DEFAULT_API_KEY = os.getenv('DOUBAO_API_KEY', '1cf58d28-bb11-4211-92c9-60001ee76343')
doubao_client = DoubaoAPI(DEFAULT_API_KEY)
```

**方法2: 创建.env文件**

```bash
# 在项目根目录创建.env文件
echo "DOUBAO_API_KEY=你的真实API密钥" > .env
```

然后安装python-dotenv:
```bash
pip install python-dotenv
```

在 `api_server_auth.py` 开头添加:
```python
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件
```

**方法3: 直接替换（测试用）**

直接修改 `doubao_api.py` 第301行:
```python
DEFAULT_API_KEY = "你的真实API密钥"
```

#### 步骤3: 验证API密钥

```bash
cd backend/src
python ai_companion/doubao_api.py
```

**预期输出**:
```
============================================================
豆包大模型API测试
============================================================
✓ 对话成功: 你好！我是豆包，一个AI助手...

豆包API模块就绪！
```

**如果失败**:
```
✗ 对话失败: 401 Unauthorized
```
说明API密钥无效，需要重新获取。

---

### 解决方案2: 前端集成AI分析按钮 ✅

当前 `student.html` 可能缺少AI深度分析按钮，需要添加。

#### 修改方案

编辑 `frontend/public/student.html`，在视频控制区域添加:

```html
<!-- 在摄像头控制按钮附近添加 -->
<div class="ai-controls">
    <button id="btnStartCamera" class="btn btn-primary">
        📹 开启摄像头
    </button>

    <button id="btnAIAnalysis" class="btn btn-success" disabled>
        🤖 AI深度分析
    </button>

    <button id="btnStopCamera" class="btn btn-secondary" disabled>
        ⏹️ 停止
    </button>
</div>

<!-- 添加分析结果显示区域 -->
<div id="aiAnalysisResult" class="ai-result-panel" style="display: none;">
    <h3>🎓 学习内容分析</h3>
    <div id="contentAnalysis"></div>

    <h3>🧘 姿势与状态分析</h3>
    <div id="stateAnalysis"></div>
</div>
```

添加JavaScript代码:

```javascript
// AI深度分析功能
document.getElementById('btnAIAnalysis').addEventListener('click', async () => {
    const btn = document.getElementById('btnAIAnalysis');
    btn.disabled = true;
    btn.textContent = '🔄 分析中...';

    try {
        // 捕获当前视频帧
        const canvas = document.createElement('canvas');
        const video = document.getElementById('videoElement');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        // 转为Base64
        const frameData = canvas.toDataURL('image/jpeg');

        // 调用高级分析API
        const response = await fetch('/api/vision/analyze_advanced', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                frame_data: frameData
            })
        });

        const result = await response.json();

        if (result.success) {
            // 显示分析结果
            document.getElementById('aiAnalysisResult').style.display = 'block';
            document.getElementById('contentAnalysis').innerHTML =
                `<pre>${JSON.stringify(result.data.learning_content, null, 2)}</pre>`;
            document.getElementById('stateAnalysis').innerHTML =
                `<pre>${JSON.stringify(result.data.posture_and_state, null, 2)}</pre>`;

            // 显示剩余时长
            const usage = result.data.usage_info;
            alert(`分析完成！\n今日已用: ${usage.today_used}秒\n剩余: ${usage.remaining_time}秒`);
        } else {
            alert('分析失败: ' + (result.detail || result.message));
        }
    } catch (error) {
        console.error('AI分析错误:', error);
        alert('网络错误，请稍后重试');
    } finally {
        btn.disabled = false;
        btn.textContent = '🤖 AI深度分析';
    }
});

// 摄像头开启后启用AI分析按钮
navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        document.getElementById('videoElement').srcObject = stream;
        document.getElementById('btnAIAnalysis').disabled = false;
    });
```

---

### 解决方案3: 添加学习总结功能 ✅

创建新按钮触发学习总结:

```html
<!-- 在学习结束后显示 -->
<button id="btnGenerateSummary" class="btn btn-primary">
    📊 生成学习总结
</button>

<div id="learningSummary" class="summary-panel" style="display: none;">
    <h2>📚 本次学习总结</h2>
    <div id="summaryContent"></div>
</div>
```

JavaScript:

```javascript
document.getElementById('btnGenerateSummary').addEventListener('click', async () => {
    const btn = document.getElementById('btnGenerateSummary');
    btn.disabled = true;
    btn.textContent = '生成中...';

    try {
        const response = await fetch('/api/learning/generate_summary', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({
                session_id: null  // 使用当前会话
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('learningSummary').style.display = 'block';
            document.getElementById('summaryContent').innerHTML =
                result.data.summary.replace(/\n/g, '<br>');
        } else {
            alert('生成失败: ' + (result.detail || result.message));
        }
    } catch (error) {
        console.error('生成总结错误:', error);
        alert('网络错误，请稍后重试');
    } finally {
        btn.disabled = false;
        btn.textContent = '📊 生成学习总结';
    }
});
```

---

### 解决方案4: 处理网络问题 ✅

#### 增加超时时间

编辑 `backend/src/ai_companion/doubao_api.py`:

```python
# 第77行，将超时从30秒增加到60秒
response = requests.post(
    f"{self.base_url}/chat/completions",
    headers=self.headers,
    json=payload,
    timeout=60  # 修改为60秒
)
```

#### 添加重试机制

```python
import time

def analyze_image_with_retry(self, image_data: str, question: str, max_retries: int = 3) -> Dict:
    """带重试机制的图片分析"""
    for attempt in range(max_retries):
        try:
            result = self.analyze_image(image_data, question)
            if "error" not in result:
                return result

            # 如果是网络错误，等待后重试
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避: 1s, 2s, 4s
        except Exception as e:
            if attempt == max_retries - 1:
                return {"error": str(e), "success": False}
            time.sleep(2 ** attempt)

    return {"error": "重试失败", "success": False}
```

---

### 解决方案5: 优化会员限制提示 ✅

修改API响应，提供更友好的提示:

```python
# api_server_auth.py 第690行
if not can_use:
    user = db.get_user_by_id(current_user.user_id)

    return JSONResponse(
        status_code=403,
        content={
            "success": False,
            "error": "今日AI分析时长已用完",
            "data": {
                "daily_limit": user.get_daily_limit(),
                "today_used": user.get_daily_limit() - remaining_time,
                "remaining_time": 0,
                "is_vip": user.is_vip(),
                "upgrade_url": "/api/membership/upgrade"
            },
            "message": "升级VIP可享受无限AI分析！"
        }
    )
```

---

## 测试与验证

### 测试1: API密钥验证

```bash
cd backend/src
python -c "
from ai_companion.doubao_api import doubao_client

result = doubao_client.chat('你好')
if result.get('success'):
    print('✅ API密钥有效')
    print(f'回复: {result[\"reply\"][:50]}...')
else:
    print('❌ API密钥无效')
    print(f'错误: {result.get(\"error\")}')
"
```

---

### 测试2: 视觉分析测试

```bash
python -c "
import base64
from ai_companion.doubao_api import doubao_client

# 读取测试图片
with open('test_image.jpg', 'rb') as f:
    img_data = base64.b64encode(f.read()).decode()

# 测试学习内容分析
result = doubao_client.analyze_learning_content(f'data:image/jpeg;base64,{img_data}')

if result.get('success'):
    print('✅ 视觉分析成功')
    print(result['analysis'])
else:
    print('❌ 视觉分析失败')
    print(result.get('error'))
"
```

---

### 测试3: 完整流程测试

1. 启动服务器:
```bash
cd backend/src
python api_server_auth.py
```

2. 登录系统: http://localhost:8000

3. 进入学习中心: http://localhost:8000/student

4. 开启摄像头

5. 点击"AI深度分析"按钮

6. **检查浏览器控制台**:
   - F12 → Network → 查找 `analyze_advanced` 请求
   - 检查状态码（应为200）
   - 查看响应内容

7. **检查服务器日志**:
   - 查看是否有错误信息
   - 检查豆包API请求日志

---

### 测试4: 会员限制测试

```bash
# 测试普通用户限制
curl -X POST http://localhost:8000/api/vision/analyze_advanced \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"frame_data": "data:image/jpeg;base64,..."}'

# 多次调用直到超过1800秒限制
# 应返回403错误
```

---

## 常见错误处理

### 错误1: 401 Unauthorized

**错误信息**:
```json
{
  "error": "401 Client Error: Unauthorized",
  "success": false
}
```

**原因**: API密钥无效或已过期

**解决**:
1. 检查API密钥是否正确
2. 登录火山引擎控制台验证密钥状态
3. 重新生成API密钥

---

### 错误2: 403 Forbidden (会员限制)

**错误信息**:
```json
{
  "success": false,
  "error": "今日AI分析时长已用完",
  "message": "升级VIP可享受无限制使用！"
}
```

**原因**: 普通用户超过每日30分钟限制

**解决**:
1. 等待第二天重置
2. 升级VIP会员:
```bash
curl -X POST http://localhost:8000/api/membership/upgrade \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
```

---

### 错误3: Timeout

**错误信息**:
```json
{
  "error": "HTTPSConnectionPool: Read timed out",
  "success": false
}
```

**原因**: 网络超时或豆包API响应慢

**解决**:
1. 增加超时时间（见解决方案4）
2. 检查网络连接
3. 使用重试机制

---

### 错误4: 无法解析响应

**错误信息**:
```json
{
  "success": false,
  "error": "无法解析响应"
}
```

**原因**: 豆包API返回格式异常

**解决**:
1. 打印原始响应查看: `print(result['raw_response'])`
2. 检查模型名称是否正确
3. 联系火山引擎技术支持

---

## 优化建议

### 优化1: 添加缓存机制

对相似的图片避免重复分析:

```python
import hashlib

def get_image_hash(image_data: str) -> str:
    """计算图片哈希"""
    return hashlib.md5(image_data.encode()).hexdigest()

# 使用Redis缓存
cached_result = redis_service.get(f"ai_analysis:{image_hash}")
if cached_result:
    return cached_result

result = doubao_client.analyze_learning_content(image_data)
redis_service.set(f"ai_analysis:{image_hash}", result, ttl=3600)
```

---

### 优化2: 异步调用

使用异步请求提升性能:

```python
import aiohttp
import asyncio

async def analyze_image_async(self, image_data: str, question: str) -> Dict:
    """异步分析图片"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            return await response.json()
```

---

### 优化3: 批量分析

一次请求分析多个方面:

```python
def analyze_comprehensive(self, image_data: str) -> Dict:
    """综合分析（一次调用）"""
    question = """请全面分析这张学习场景图片：

1. 学习内容分析:
   - 学科和主题
   - 难度级别
   - 学习阶段

2. 姿势与状态分析:
   - 坐姿评分
   - 专注度
   - 情绪状态

3. 改进建议:
   - 学习方法建议
   - 姿势调整建议
   - 下一步学习方向

请用JSON格式返回完整结果。"""

    return self.analyze_image(image_data, question)
```

---

### 优化4: 使用WebSocket实时推送

避免前端轮询，改用WebSocket推送:

```python
# 后端
@app.websocket("/ws/ai_analysis/{token}")
async def ai_analysis_ws(websocket: WebSocket, token: str):
    await websocket.accept()

    while True:
        # 接收图片数据
        data = await websocket.receive_json()

        # 分析
        result = doubao_client.analyze_learning_content(data['frame'])

        # 推送结果
        await websocket.send_json(result)
```

```javascript
// 前端
const ws = new WebSocket(`ws://localhost:8000/ws/ai_analysis/${token}`);

ws.onmessage = (event) => {
    const result = JSON.parse(event.data);
    displayAnalysisResult(result);
};

// 发送帧数据
ws.send(JSON.stringify({ frame: frameData }));
```

---

### 优化5: 添加使用统计

记录API调用情况:

```python
# 添加统计表
class AIUsageStats(Base):
    __tablename__ = 'ai_usage_stats'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    api_type = Column(String(50))  # analyze_content, analyze_state, summary
    success = Column(Boolean)
    duration = Column(Float)  # 调用耗时
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
```

---

## 完整配置检查清单

### 后端配置

- [ ] 豆包API密钥已配置
- [ ] API密钥已验证有效
- [ ] Redis服务已启动（可选）
- [ ] 数据库已初始化
- [ ] 依赖包已安装 (`requests`, `opencv-python`, `mediapipe`)

### 前端配置

- [ ] 学习页面有AI分析按钮
- [ ] 摄像头权限已授予
- [ ] 静态文件正常加载
- [ ] Token认证正常

### 测试验证

- [ ] API密钥测试通过
- [ ] 文本对话测试通过
- [ ] 视觉分析测试通过
- [ ] 学习总结测试通过
- [ ] 会员限制测试通过

---

## 快速诊断命令

### 检查API密钥

```bash
cd backend/src
python -c "from ai_companion.doubao_api import doubao_client; print('API Key:', doubao_client.api_key[:8] + '...')"
```

### 测试基础连接

```bash
curl -X POST https://ark.cn-beijing.volces.com/api/v3/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "doubao-seed-1-6-vision-250815",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 查看用户剩余时长

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/membership/status
```

---

## 总结

### 核心问题

"打开网页时不能正常调用豆包大模型API"的根本原因是:

1. **API密钥配置** - 默认密钥可能无效
2. **前端未集成** - 网页打开后不会自动调用，需要用户手动触发
3. **缺少UI入口** - 学习页面可能缺少"AI分析"按钮
4. **会员限制** - 普通用户有使用时长限制

### 解决步骤

1. ✅ 配置有效的豆包API密钥
2. ✅ 在学习页面添加"AI深度分析"按钮
3. ✅ 实现前端调用逻辑
4. ✅ 添加友好的错误提示
5. ✅ 测试验证功能正常

### 重要提醒

⚠️ **豆包API不会在"打开网页时"自动调用**

这是设计如此，原因:
- AI分析消耗API配额和费用
- 需要用户明确授权
- 避免浪费资源
- 符合隐私保护原则

用户需要**主动点击"AI分析"按钮**才会调用豆包API。

---

**文档版本**: 1.0
**最后更新**: 2025-11-03
**维护者**: AI Learning Companion Team
