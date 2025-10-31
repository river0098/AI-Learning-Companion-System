# 🚀 快速入门指南 - AI 学习伙伴系统

## 5 分钟演示

### 步骤 1：安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 系统: venv\Scripts\activate

# 安装依赖包
pip install -r requirements.txt
```

### 步骤 2：运行演示

```bash
cd backend/src
python main.py
```

你应该会看到类似以下的输出：

```
============================================================
AI 学习伙伴系统
将监督转变为智能陪伴
============================================================

🚀 正在初始化 AI 学习伙伴系统...
✅ 系统初始化成功！

✓ 会话已开始: session_student_demo_001_1234567890.0

📊 系统正在监控和分析...
   - 视觉：检测姿势、注视、情绪
   - OCR：准备识别内容
   - AI 伙伴：监控干预时机
   - 时间追踪：记录学习模式

💬 学生消息: '我不理解这道题'
🤖 AI 伙伴（导师模式）：我来帮你！这道题具体哪里让你困惑？

📊 正在生成仪表板...
   学生：0 天连续记录，0 项成就
   家长：低参与度，0.5% 生产力

✓ 会话已结束: 0秒专注时间

✅ 系统清理成功

============================================================
系统演示完成！
============================================================
```

### 步骤 3：测试单个模块

```bash
# 测试视觉分析
python backend/src/vision/vision_analyzer.py

# 测试 OCR
python backend/src/ocr/text_recognizer.py

# 测试知识图谱
python backend/src/knowledge_graph/graph_engine.py

# 测试时间追踪
python backend/src/time_tracking/tracker.py

# 测试 AI 伙伴
python backend/src/ai_companion/companion.py

# 测试仪表板
python backend/src/dashboard/generator.py
```

每个模块都有一个 `if __name__ == "__main__"` 代码块，其中包含示例用法。

---

## 快速集成示例

```python
from main import AILearningCompanion
import numpy as np

# 初始化
companion = AILearningCompanion()

# 开始会话
session = companion.start_session("student_001")
print(f"已开始: {session['session_id']}")

# 模拟相机帧
frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = companion.process_frame(frame)

# 学生交互
response = companion.student_message(
    "我卡在这道题上了",
    mode="guide"
)
print(f"AI: {response['ai_message']}")

# 记录练习结果
companion.record_exercise_result(
    concept_id="math_arithmetic_addition",
    correct=True,
    time_spent=120
)

# 获取仪表板
student_dash = companion.get_student_dashboard("student_001")
parent_dash = companion.get_parent_dashboard("student_001")

# 结束会话
summary = companion.end_session()
print(f"专注时间: {summary['focused_time']}秒")

# 清理
companion.cleanup()
```

---

## 配置

编辑 `config/settings.yaml` 来自定义行为：

```yaml
# 关键设置
camera:
  sample_interval: 3  # 帧分析之间的秒数

vision:
  enable_emotion_recognition: true
  confidence_threshold: 0.5

ai_companion:
  personality: "encouraging"  # encouraging（鼓励型）, strict（严格型）, playful（活泼型）
  default_mode: "coach"  # guide（导师）, coach（教练）, friend（朋友）

privacy:
  save_raw_images: false  # 为保护隐私，始终为 false
```

---

## 下一步

1. **连接真实相机**：修改 `main.py` 以使用实际相机
2. **添加 OCR 集成**：安装 PaddleOCR 或 Google Vision API
3. **构建 Web 界面**：创建 React 前端（即将推出）
4. **部署**：在边缘设备上设置（树莓派、Jetson Nano）

---

## 故障排除

### MediaPipe 安装问题

```bash
pip install mediapipe --upgrade
```

### OpenCV 相机访问

```bash
# Linux：将用户添加到 video 组
sudo usermod -a -G video $USER

# 测试相机
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### PaddleOCR 设置

```bash
pip install paddlepaddle paddleocr

# 测试 OCR
python -c "from paddleocr import PaddleOCR; print('OK')"
```

---

## 演示场景

### 场景 1：作业助手

```python
# 学生做数学作业
companion.start_session("alice")

# 在同一道题上 5 分钟后检测到困惑
# AI 介入："需要关于这个方程的提示吗？"

# 学生接受帮助
response = companion.student_message("是的，请", mode="guide")
# AI："先考虑分离变量..."
```

### 场景 2：专注力教练

```python
# 追踪 25 分钟专注会话
# 25 分钟后，AI 建议："专注得很好！休息 5 分钟？"

# 追踪几天的生产力
dashboard = companion.get_student_dashboard("alice")
print(f"连续记录: {dashboard['streak']} 天")
```

### 场景 3：家长洞察

```python
# 家长查看每周进度（无实时监控）
parent_view = companion.get_parent_dashboard("alice")
print(parent_view['summary'])
# "本周，您的孩子学习了 180 分钟。
#  他们在数学方面表现出强劲的进步。"
```

---

**准备好改变学习方式了吗？开始体验吧！** 🎓✨
