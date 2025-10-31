# 🎓 AI陪伴学习系统
### 将传统监督转变为智能陪伴

一个先进的AI驱动学习伙伴，使用计算机视觉、自然语言处理和情感智能来支持学生的学习旅程。

---

## 🌟 系统概述

**AI陪伴学习系统**是一个隐私优先、富有同理心的教育AI，它可以：

- 📹 **监测学习行为**：通过非侵入式相机采样
- 📝 **理解学习内容**：通过OCR和手写识别
- 🧠 **构建知识图谱**：跟踪掌握度并推荐学习路径
- ⏱️ **追踪时间和专注度**：测量生产力并发现模式
- 🤖 **提供陪伴**：具有情境感知和情感智能的交互
- 📊 **生成洞察**：通过学生和家长仪表板

### 核心差异化：真正的陪伴，而非监控

与传统监控系统不同，我们的AI伙伴：
- ✅ **鼓励**而非批评
- ✅ **理解情绪**并给予同理心回应
- ✅ **保护隐私**只存储特征，不存储原始图像
- ✅ **适应学生**提供个性化学习路径
- ✅ **赋能家长**提供洞察而非实时监控

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    AI陪伴学习系统                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📥 输入层                                                    │
│  ├─ 相机（俯视桌面，每2-5秒1帧）                             │
│  ├─ 屏幕/内容捕获（OCR就绪）                                 │
│  └─ 传感器数据（笔、键盘、鼠标）                             │
│                                                              │
│  🤖 AI引擎                                                   │
│  ├─ 视觉分析（姿势、视线、情绪）                             │
│  ├─ OCR与手写识别                                            │
│  ├─ 知识图谱（主题映射）                                     │
│  ├─ 时间追踪与行为检测                                       │
│  └─ AI伙伴（导师/教练/朋友模式）                             │
│                                                              │
│  💾 存储（隐私安全）                                         │
│  ├─ 仅特征向量（无原始图像）                                 │
│  ├─ 学习进度数据库                                           │
│  └─ 加密本地存储                                             │
│                                                              │
│  📊 输出层                                                   │
│  ├─ 学生仪表板（详细、实时）                                 │
│  ├─ 家长仪表板（汇总、隐私安全）                             │
│  └─ AI聊天界面（语音/文本）                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

详细设计文档请参见 [ARCHITECTURE.md](ARCHITECTURE.md)

---

## ✨ 核心功能

### 1. 视觉分析
- **姿势检测**：识别端正、驼背或倾斜姿势
- **视线追踪**：检测学生是否看桌面、屏幕或其他地方
- **情绪识别**：识别专注、困惑、疲惫、中性状态
- **活动水平**：测量动作和参与度
- **手部追踪**：检测书写和用笔活动

### 2. OCR与内容理解
- **多语言**：支持中文和英文
- **手写识别**：分析学生的书面作业
- **数学方程检测**：识别和解析数学符号
- **练习提取**：识别题号和问题
- **主题分类**：按学科和章节自动标记内容

### 3. 知识图谱
- **概念映射**：构建学科→章节→主题→概念层次结构
- **前置知识追踪**：理解概念依赖关系
- **掌握度计算**：跟踪理解水平（0-100%）
- **学习路径**：生成个性化学习序列
- **弱项检测**：识别需要复习的概念

### 4. 时间追踪与行为分析
- **状态检测**：活跃、空闲、分心、疲劳、休息
- **专注时间测量**：追踪有效学习时间 vs. 空闲时间
- **模式分析**：识别高效学习时段
- **连续打卡**：追踪连续学习天数
- **生产力指标**：全面的表现分析

### 5. AI伙伴（多模式）

#### 🎓 导师模式
- 解释困难概念
- 提供提示而不直接给答案
- 采用苏格拉底式提问
- *示例："这道方程组你试过消元法了吗？"*

#### 💪 教练模式
- 追踪进度并庆祝成就
- 设定微目标和挑战
- 提供激励性反馈
- *示例："你今天比昨天多学了12分钟——保持这个势头！"*

#### 🤗 朋友模式
- 提供情感支持
- 在需要时建议休息
- 给予共情回应
- *示例："你已经学习90分钟了，要不要起来活动一下？"*

### 6. 隐私安全的仪表板

#### 学生仪表板
- 每日/每周/每月学习时间
- 主题掌握度雷达图
- 近期成就和连续打卡
- AI对话历史
- 个性化推荐

#### 家长仪表板
- 汇总的周/月总结（无实时监控）
- 按学科分类的进度
- AI生成的洞察
- 生产力和一致性评分
- 支持建议

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- 兼容OpenCV的摄像头
- （可选）支持CUDA的GPU用于加速

### 安装

1. **克隆仓库**
   ```bash
   git clone https://github.com/river0098/AI-Learning-Companion-System.git
   cd AI-Learning-Companion-System
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境**
   ```bash
   cp .env.example .env
   # 编辑.env文件配置你的设置
   ```

5. **初始化数据目录**
   ```bash
   mkdir -p data/models data/samples logs
   ```

### 快速运行

#### 运行主应用

```bash
cd backend/src
python main.py
```

#### 测试各个模块

```bash
# 测试视觉分析
python backend/src/vision/vision_analyzer.py

# 测试OCR
python backend/src/ocr/text_recognizer.py

# 测试知识图谱
python backend/src/knowledge_graph/graph_engine.py

# 测试时间追踪
python backend/src/time_tracking/tracker.py

# 测试AI伙伴
python backend/src/ai_companion/companion.py

# 测试仪表板生成器
python backend/src/dashboard/generator.py
```

#### 使用示例

```python
from main import AILearningCompanion

# 初始化系统
system = AILearningCompanion()

# 开始学习会话
session = system.start_session("student_001")

# 处理相机帧（模拟）
import numpy as np
frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = system.process_frame(frame)

# 学生寻求帮助
response = system.student_message(
    "我不理解这道题",
    mode="guide"
)
print(f"AI: {response['ai_message']}")

# 获取学生仪表板
dashboard = system.get_student_dashboard("student_001")
print(f"今天学习时间: {dashboard['today_minutes']} 分钟")

# 获取家长仪表板（隐私安全）
parent_view = system.get_parent_dashboard("student_001")
print(f"每周总结: {parent_view['summary']}")

# 结束会话
summary = system.end_session()
print(f"会话完成: 专注时间{summary['focused_time']}秒")

# 清理
system.cleanup()
```

---

## 📁 项目结构

```
AI-Learning-Companion-System/
├── backend/
│   ├── src/
│   │   ├── vision/              # 计算机视觉分析
│   │   │   └── vision_analyzer.py
│   │   ├── ocr/                 # OCR与手写识别
│   │   │   └── text_recognizer.py
│   │   ├── knowledge_graph/     # 知识映射引擎
│   │   │   └── graph_engine.py
│   │   ├── time_tracking/       # 时间与行为追踪
│   │   │   └── tracker.py
│   │   ├── ai_companion/        # AI聊天伙伴
│   │   │   └── companion.py
│   │   ├── dashboard/           # 仪表板生成
│   │   │   └── generator.py
│   │   ├── storage/             # 数据持久化
│   │   ├── utils/               # 工具函数
│   │   └── main.py              # 主应用程序
│   └── tests/                   # 单元测试
│
├── frontend/                    # Web界面（未来）
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── public/
│
├── config/
│   └── settings.yaml            # 系统配置
│
├── data/
│   ├── models/                  # 预训练模型
│   └── samples/                 # 示例数据
│
├── docs/                        # 额外文档
│
├── scripts/                     # 实用脚本
│
├── ARCHITECTURE.md              # 详细架构
├── README.md                    # 本文件
├── QUICKSTART.md                # 快速开始指南
├── requirements.txt             # Python依赖
└── .env.example                 # 环境变量模板
```

---

## 🔒 隐私与安全

### 核心原则

1. **不存储视频**：绝不保存原始相机录像
2. **仅提取特征**：只存储AI提取的特征
3. **本地优先**：默认情况下所有处理在设备上进行
4. **加密存储**：数据库使用静态加密
5. **匿名化家长视图**：家长只看汇总数据，不看实时监控
6. **用户控制**：学生可随时暂停/禁用监控

### 数据生命周期

```
相机帧 → 特征提取 → 分析 → 存储
   ↓         ↓       ↓      ↓
(丢弃)   (仅特征)  (洞察) (加密)
```

### 合规性

- GDPR友好（数据最小化、用户控制）
- COPPA合规（家长同意、适龄）
- FERPA对齐（教育隐私）

---

## 🎯 AI伙伴交互示例

### 场景1：检测到分心
```
[学生看向别处3分钟]

AI（朋友模式）："你已经有3分钟没动了，需要休息一下吗？
                 还是有什么事情让你分心了？"

快捷回复：[是的，休息一下] [不，继续学习] [再给我5分钟]
```

### 场景2：困惑检测
```
[OCR检测到同一道题多次尝试，面部表情：困惑]

AI（导师模式）："我注意到你在这道二次方程上花了不少功夫。
                 要不要一个提示？可以先试试因式分解。"

快捷回复：[是的，讲解更多] [给个例子] [我自己想想]
```

### 场景3：成就庆祝
```
[学生完成10道题，保持45分钟专注]

AI（教练模式）："哇！你刚刚完成了10道题，还保持了45分钟的
                 高度专注——这是你的新纪录！🎉"

快捷回复：[谢谢！] [设定新目标] [休息一下]
```

### 场景4：疲劳检测
```
[驼背姿势，检测到打哈欠，连续学习90分钟]

AI（朋友模式）："你已经连续学习90分钟了，大脑需要休息！
                 要不要出去走5分钟？"

快捷回复：[好主意] [再坚持10分钟] [我还好]
```

---

## 📊 仪表板预览

### 学生仪表板功能
- ⏱️ **时间可视化**：每日/每周学习时间图表
- 📈 **进度追踪**：主题掌握度雷达图
- 🏆 **成就**：徽章和连续打卡
- 💬 **AI聊天历史**：近期伙伴互动
- 🎯 **推荐**：个性化的下一步

### 家长仪表板功能
- 📅 **每周总结**：汇总学习时间
- 📚 **学科进度**：按主题分类的掌握水平
- 💡 **AI洞察**："您的孩子在数学方面进步显著"
- 📊 **趋势**：4周进度可视化
- ✅ **建议**：支持建议

---

## 🛠️ 配置

编辑 `config/settings.yaml` 来自定义：

- **隐私**：启用/禁用功能、数据保留
- **相机**：设备ID、分辨率、采样率
- **视觉**：检测阈值、启用的功能
- **OCR**：语言支持、识别引擎
- **AI伙伴**：个性、干预规则
- **仪表板**：更新间隔、导出格式

所有选项请参见 [settings.yaml](config/settings.yaml)

---

## 🧪 测试

```bash
# 运行所有测试
pytest backend/tests/

# 测试特定模块
pytest backend/tests/test_vision.py

# 带覆盖率
pytest --cov=backend/src backend/tests/
```

---

## 🌐 API文档

（未来：REST API和WebSocket端点）

### 计划的端点

- `POST /session/start` - 开始学习会话
- `POST /session/end` - 结束会话
- `POST /frame/analyze` - 分析相机帧
- `POST /content/recognize` - OCR内容识别
- `POST /chat/message` - 向AI伙伴发送消息
- `GET /dashboard/student` - 获取学生仪表板
- `GET /dashboard/parent` - 获取家长仪表板
- `WS /live` - 实时更新的WebSocket

---

## 🚧 路线图

### 版本1.0（当前）
- ✅ 核心视觉分析
- ✅ OCR和手写识别
- ✅ 知识图谱引擎
- ✅ 时间追踪和行为检测
- ✅ 具有3种模式的AI伙伴
- ✅ 学生和家长仪表板

### 版本2.0（计划中）
- 🔲 基于Web的UI（React前端）
- 🔲 FastAPI REST API
- 🔲 实时WebSocket通知
- 🔲 语音交互支持
- 🔲 多学生教室模式
- 🔲 高级情绪识别

### 版本3.0（未来）
- 🔲 游戏化和徽章系统
- 🔲 桌面投影AR覆盖
- 🔲 与学习平台集成
- 🔲 家长移动应用
- 🔲 高级分析和预测
- 🔲 协作学习功能

---

## 🤝 贡献

我们欢迎贡献！请参见 [CONTRIBUTING.md](CONTRIBUTING.md)（即将推出）了解指南。

### 开发设置

1. Fork仓库
2. 创建功能分支（`git checkout -b feature/amazing-feature`）
3. 进行更改
4. 运行测试（`pytest`）
5. 格式化代码（`black backend/`）
6. 提交（`git commit -m '添加精彩功能'`）
7. 推送（`git push origin feature/amazing-feature`）
8. 打开Pull Request

---

## 📄 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- **MediaPipe** - Google的计算机视觉框架
- **PaddleOCR** - 多语言OCR工具包
- **NetworkX** - 图分析库
- **OpenCV** - 计算机视觉库
- 关于学习模式和动机的教育心理学研究

---

## 📞 支持

- **问题**：[GitHub Issues](https://github.com/river0098/AI-Learning-Companion-System/issues)
- **讨论**：[GitHub Discussions](https://github.com/river0098/AI-Learning-Companion-System/discussions)
- **邮箱**：support@ailearningcompanion.example.com

---

## 🌟 Star历史

如果你觉得这个项目有用，请考虑给它一个star！⭐

---

## 📖 引用

如果你在研究或教育中使用这个系统，请引用：

```bibtex
@software{ai_learning_companion_2025,
  title = {AI陪伴学习系统},
  author = {AI陪伴学习团队},
  year = {2025},
  url = {https://github.com/river0098/AI-Learning-Companion-System}
}
```

---

**用❤️为学生打造，由教育工作者和AI研究人员开发**

*将监督转变为陪伴。用同理心赋能学习。*
