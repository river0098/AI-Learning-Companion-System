# 会员系统和AI分析使用指南

## 📋 目录

1. [会员系统概述](#会员系统概述)
2. [普通会员 vs VIP会员](#普通会员-vs-vip会员)
3. [豆包大模型集成](#豆包大模型集成)
4. [API接口说明](#api接口说明)
5. [使用示例](#使用示例)
6. [常见问题](#常见问题)

---

## 会员系统概述

AI陪伴学习系统现已集成完整的会员分级系统，支持普通会员和VIP会员两种类型。系统使用豆包大模型提供高级AI分析功能。

### 会员类型

- **普通会员（Free）**：免费注册，每天享受30分钟AI大模型分析
- **VIP会员（VIP）**：付费升级，无限制使用AI大模型分析

---

## 普通会员 vs VIP会员

### 功能对比表

| 功能 | 普通会员 | VIP会员 |
|------|---------|--------|
| 基础视觉分析（MediaPipe） | ✅ 无限制 | ✅ 无限制 |
| 姿势、视线、情绪检测 | ✅ 无限制 | ✅ 无限制 |
| AI伙伴对话 | ✅ 无限制 | ✅ 无限制 |
| 学习时间跟踪 | ✅ 无限制 | ✅ 无限制 |
| **AI大模型深度分析** | ⚠️ 每天30分钟 | ✅ 无限制 |
| 学习内容识别（OCR增强） | ⚠️ 每天30分钟 | ✅ 无限制 |
| 智能学习总结 | ⚠️ 消耗配额 | ✅ 无限制 |
| 学科和难度识别 | ⚠️ 每天30分钟 | ✅ 无限制 |
| 优先客服支持 | ❌ | ✅ |

### 使用配额说明

#### 普通会员
- **每日配额**：1800秒（30分钟）
- **计费方式**：
  - 每次高级AI分析消耗 3秒
  - 生成学习总结消耗 5秒
- **配额重置**：每天0点自动重置

#### VIP会员
- **每日配额**：无限制（-1 表示无限）
- **有效期**：根据购买时长（默认30天）
- **自动续费**：需要手动续费（可在系统中设置）

---

## 豆包大模型集成

### 功能介绍

本系统集成了字节跳动的豆包大模型（Doubao），提供以下高级AI分析功能：

#### 1. 学习内容深度分析
```python
# 功能：分析学生正在学习的具体内容
- 识别学科（数学、语文、英语等）
- 识别具体主题和知识点
- 判断学习难度级别
- 识别学习材料类型
- 检测学习阶段（预习/学习/练习/复习）
```

#### 2. 姿势和状态智能分析
```python
# 功能：分析学习姿势和精神状态
- 坐姿是否正确（距离、角度、背部）
- 精神状态评估（专注/疲劳/困惑/分心）
- 不良学习习惯检测
- 情绪状态识别
- 学习投入度评估
```

#### 3. 智能学习总结
```python
# 功能：生成个性化学习总结报告
- 学习效果评估
- 专注度分析和改进建议
- 学习姿势健康提醒
- 内容掌握情况推测
- 下次学习建议
- 鼓励和激励语
```

### 技术特点

- **模型**：doubao-seed-1-6-251015
- **推理强度**：支持 low/medium/high 三档
- **最大输出**：65535 tokens
- **多模态支持**：同时处理图片和文本
- **响应时间**：平均 2-5秒

---

## API接口说明

### 1. 获取会员状态

```http
GET /api/membership/status
Authorization: Bearer {token}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "is_vip": false,
    "membership_type": "free",
    "membership_expires": null,
    "daily_limit": 1800,
    "today_used": 120,
    "remaining_time": 1680,
    "can_use_ai": true,
    "benefits": {
      "free": [
        "每天30分钟AI分析",
        "基础学习跟踪",
        "AI伙伴对话"
      ],
      "vip": [
        "无限AI分析时长",
        "深度学习内容识别",
        "智能学习总结",
        "优先客服支持"
      ]
    }
  }
}
```

### 2. 升级VIP会员

```http
POST /api/membership/upgrade
Authorization: Bearer {token}
Content-Type: application/json

{
  "days": 30
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "成功升级为VIP会员！有效期：30天",
  "data": {
    "membership_type": "vip",
    "membership_expires": "2025-12-03T10:00:00",
    "daily_limit": -1
  }
}
```

### 3. 高级AI分析（消耗配额）

```http
POST /api/vision/analyze_advanced
Authorization: Bearer {token}
Content-Type: application/json

{
  "frame_data": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "learning_content": {
      "success": true,
      "analysis": "学生正在学习高中数学，具体内容为三角函数..."
    },
    "posture_and_state": {
      "success": true,
      "analysis": "坐姿良好，精神状态专注，建议继续保持..."
    },
    "usage_info": {
      "is_vip": false,
      "today_used": 3,
      "remaining_time": 1677,
      "can_continue": true
    }
  }
}
```

### 4. 生成学习总结

```http
POST /api/learning/generate_summary
Authorization: Bearer {token}
Content-Type: application/json

{
  "session_id": "optional_session_id"
}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "summary": "本次学习表现优秀！\n\n1. 学习效果评估：良好\n2. 专注度：85%，建议减少环境干扰\n3. 学习姿势：整体良好，注意保持距离\n4. 内容掌握：对三角函数基本概念掌握扎实\n5. 下次建议：可以尝试更多应用题练习\n\n继续保持这个状态，你一定会取得更大进步！💪",
    "session_data": {
      "duration": 45,
      "topics": ["三角函数", "数学"],
      "focus_level": 85,
      "posture_scores": [75, 80, 85],
      "detected_content": "高中数学"
    }
  }
}
```

### 5. 获取用户信息（含会员状态）

```http
GET /api/auth/me
Authorization: Bearer {token}
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "username": "student123",
    "membership_type": "free",
    "is_vip": false,
    "daily_limit": 1800,
    "today_usage": 120,
    "remaining_time": 1680,
    "can_use": true
  }
}
```

---

## 使用示例

### 场景1：学生日常使用

```javascript
// 1. 登录后自动加载会员状态
async function loadMembershipStatus() {
    const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await response.json();

    if (result.data.is_vip) {
        console.log('您是VIP会员，无限制使用AI分析');
    } else {
        console.log(`剩余AI分析时长：${result.data.remaining_time}秒`);
    }
}

// 2. 使用高级AI分析（自动检查配额）
async function analyzeWithAI(frameData) {
    try {
        const response = await fetch('/api/vision/analyze_advanced', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ frame_data: frameData })
        });

        const result = await response.json();

        if (result.success) {
            console.log('学习内容：', result.data.learning_content);
            console.log('剩余时长：', result.data.usage_info.remaining_time);
        }
    } catch (error) {
        if (error.status === 403) {
            alert('今日AI分析时长已用完，升级VIP可无限使用！');
        }
    }
}

// 3. 结束学习后生成总结
async function generateSummary() {
    const response = await fetch('/api/learning/generate_summary', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    });

    const result = await response.json();
    if (result.success) {
        console.log('学习总结：', result.data.summary);
    }
}
```

### 场景2：VIP升级流程

```javascript
// 用户点击升级按钮
async function upgradeToVIP() {
    // 1. 显示确认对话框
    if (!confirm('升级为VIP会员？费用：30天/99元')) {
        return;
    }

    // 2. 调用升级接口（实际应用需要集成支付）
    const response = await fetch('/api/membership/upgrade', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ days: 30 })
    });

    const result = await response.json();

    if (result.success) {
        alert('🎉 升级成功！现在您可以无限制使用AI分析功能！');
        loadMembershipStatus();  // 刷新会员状态
    }
}
```

### 场景3：Python后端集成

```python
from ai_companion.doubao_api import doubao_client

# 分析学习内容
result = doubao_client.analyze_learning_content(
    image_data="data:image/jpeg;base64,..."
)

if result.get("success"):
    print("学科：", result["analysis"])

# 生成学习总结
summary = doubao_client.generate_learning_summary({
    "duration": 45,
    "topics": ["数学", "三角函数"],
    "focus_level": 85
})

print("总结：", summary["summary"])
```

---

## 常见问题

### Q1: 如何查看我的剩余AI分析时长？

**A**: 登录后，在右侧仪表板的"⚡ AI分析配额"区域可以看到：
- 今日已用时长
- 剩余时长
- 使用进度条

### Q2: 普通会员每天30分钟够用吗？

**A**: 对于大多数学生足够用：
- 每次AI分析消耗3秒
- 30分钟 = 1800秒
- 可以进行约 **600次** AI分析
- 如果每3秒分析一次，可以持续使用约 **30分钟**

### Q3: VIP会员如何收费？

**A**: 本系统为演示版本，VIP升级功能已实现，但未集成支付系统。实际部署时建议：
- 按月订阅：99元/月
- 按季订阅：279元/季（省20元）
- 按年订阅：999元/年（省189元）

### Q4: 基础视觉分析和高级AI分析有什么区别？

**A**:

| 功能 | 基础分析 | 高级AI分析 |
|------|---------|-----------|
| 技术 | MediaPipe（本地） | 豆包大模型（云端） |
| 消耗配额 | 不消耗 | 消耗配额 |
| 姿势检测 | ✅ | ✅ 更精准 |
| 视线追踪 | ✅ | ✅ 更准确 |
| 情绪识别 | ✅ 基础 | ✅ 深度分析 |
| 内容识别 | ❌ | ✅ OCR + 理解 |
| 学科识别 | ❌ | ✅ 智能识别 |
| 学习建议 | ❌ | ✅ 个性化建议 |

**建议**：
- 日常学习：使用基础分析（不消耗配额）
- 需要详细反馈时：使用高级AI分析
- 学习结束时：生成智能总结

### Q5: 配额用完了怎么办？

**A**: 有三个选择：
1. **等待重置**：每天0点自动重置为30分钟
2. **升级VIP**：享受无限制使用
3. **使用基础分析**：不消耗配额，功能仍然强大

### Q6: 如何更换豆包API密钥？

**A**: 编辑 `backend/src/ai_companion/doubao_api.py`：

```python
# 修改这一行
DEFAULT_API_KEY = "your_api_key_here"
```

或使用环境变量：
```bash
export DOUBAO_API_KEY="your_api_key_here"
```

### Q7: VIP会员到期后会怎样？

**A**:
- VIP到期后自动降级为普通会员
- 历史数据不会丢失
- 可以继续使用所有基础功能
- AI分析将受到每天30分钟的限制

### Q8: 可以多设备同时使用吗？

**A**:
- **普通会员**：配额在所有设备间共享
- **VIP会员**：支持多设备同时登录，无限制使用

### Q9: 如何获取API密钥？

**A**:
1. 访问豆包开放平台：https://www.volcengine.com/
2. 注册账号并实名认证
3. 创建应用获取API密钥
4. 配置到系统中

### Q10: 系统如何保护隐私？

**A**:
- ✅ 不保存原始视频和图片
- ✅ 只保存分析结果（特征向量）
- ✅ 豆包API调用使用HTTPS加密
- ✅ 用户数据本地数据库存储
- ✅ 可随时删除所有数据

---

## 技术支持

如有问题，请通过以下方式联系：

- **GitHub Issues**: [提交问题](https://github.com/yourusername/AI-Learning-Companion-System/issues)
- **文档**: 查看完整使用指南.md
- **API文档**: http://localhost:8000/docs （启动服务器后访问）

---

## 更新日志

### v2.1.0 (2025-11-03)
- ✅ 新增会员分级系统
- ✅ 集成豆包大模型
- ✅ 新增AI使用配额跟踪
- ✅ 新增VIP升级功能
- ✅ 新增学习内容深度分析
- ✅ 新增智能学习总结

### v2.0.0 (2025-11-01)
- ✅ 完整认证系统
- ✅ Web摄像头集成
- ✅ 实时AI分析

---

**祝学习愉快！🎓**
