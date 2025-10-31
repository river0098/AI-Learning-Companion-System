# 🎓 AI Learning Companion System
### Transform Traditional Supervision into Intelligent Companionship

An advanced AI-powered learning companion that uses computer vision, natural language processing, and emotional intelligence to support students through their learning journey.

---

## 🌟 Overview

The **AI Learning Companion System** is a privacy-first, empathetic educational AI that:

- 📹 **Monitors learning behavior** through non-invasive camera sampling
- 📝 **Understands study content** via OCR and handwriting recognition
- 🧠 **Builds knowledge graphs** to track mastery and suggest learning paths
- ⏱️ **Tracks time and focus** to measure productivity and detect patterns
- 🤖 **Provides companionship** with context-aware, emotionally intelligent interactions
- 📊 **Generates insights** through student and parent dashboards

### Key Differentiator: True Companionship, Not Surveillance

Unlike traditional monitoring systems, our AI companion:
- ✅ **Encourages** rather than criticizes
- ✅ **Understands emotions** and responds empathetically
- ✅ **Protects privacy** by storing only features, not raw images
- ✅ **Adapts to the student** with personalized learning paths
- ✅ **Empowers parents** with insights, not live surveillance

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI LEARNING COMPANION                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📥 INPUT LAYER                                              │
│  ├─ Camera (hovering desk view, 1 frame/2-5s)              │
│  ├─ Screen/Content capture (OCR-ready)                      │
│  └─ Sensor data (pen, keyboard, mouse)                      │
│                                                              │
│  🤖 AI ENGINE                                                │
│  ├─ Vision Analysis (posture, gaze, emotion)                │
│  ├─ OCR & Handwriting Recognition                           │
│  ├─ Knowledge Graph (topic mapping)                         │
│  ├─ Time Tracking & Behavior Detection                      │
│  └─ AI Companion (Guide/Coach/Friend modes)                 │
│                                                              │
│  💾 STORAGE (Privacy-Safe)                                   │
│  ├─ Feature vectors only (no raw images)                    │
│  ├─ Learning progress database                              │
│  └─ Encrypted local storage                                 │
│                                                              │
│  📊 OUTPUT LAYER                                             │
│  ├─ Student Dashboard (detailed, real-time)                 │
│  ├─ Parent Dashboard (aggregated, privacy-safe)             │
│  └─ AI Chat Interface (voice/text)                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

---

## ✨ Features

### 1. Vision Analysis
- **Posture Detection**: Identifies upright, slouched, or leaning positions
- **Gaze Tracking**: Detects if student is looking at desk, screen, or away
- **Emotion Recognition**: Recognizes focused, confused, tired, neutral states
- **Activity Level**: Measures movement and engagement
- **Hand Tracking**: Detects writing and pen activity

### 2. OCR & Content Understanding
- **Multi-language**: Supports English and Chinese
- **Handwriting Recognition**: Analyzes student's written work
- **Math Equation Detection**: Recognizes and parses mathematical notation
- **Exercise Extraction**: Identifies problem numbers and questions
- **Topic Classification**: Auto-tags content by subject and chapter

### 3. Knowledge Graph
- **Concept Mapping**: Builds subject → chapter → topic → concept hierarchy
- **Prerequisite Tracking**: Understands concept dependencies
- **Mastery Calculation**: Tracks understanding level (0-100%)
- **Learning Paths**: Generates personalized study sequences
- **Weak Area Detection**: Identifies concepts needing review

### 4. Time Tracking & Behavior
- **State Detection**: Active, Idle, Distracted, Fatigued, Break
- **Focus Time Measurement**: Tracks productive vs. idle time
- **Pattern Analysis**: Identifies peak productivity hours
- **Streak Tracking**: Consecutive days of study
- **Productivity Metrics**: Comprehensive performance analysis

### 5. AI Companion (Multi-Mode)

#### 🎓 Guide Mode
- Explains difficult concepts
- Provides hints without giving away answers
- Asks Socratic questions
- *Example: "Have you tried the elimination method for this system of equations?"*

#### 💪 Coach Mode
- Tracks progress and celebrates achievements
- Sets micro-goals and challenges
- Provides motivational feedback
- *Example: "You've studied 12 minutes longer than yesterday—great momentum!"*

#### 🤗 Friend Mode
- Offers emotional support
- Suggests breaks when needed
- Provides empathetic responses
- *Example: "You've been at this for 90 minutes. Want to stretch for a minute?"*

### 6. Privacy-Safe Dashboards

#### Student Dashboard
- Daily/weekly/monthly study time
- Topic mastery radar chart
- Recent achievements and streaks
- AI conversation history
- Personalized recommendations

#### Parent Dashboard
- Aggregated weekly/monthly summaries
- Subject-wise progress (no live feed)
- AI-generated insights
- Productivity and consistency scores
- Recommendations for support

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- OpenCV compatible camera
- (Optional) CUDA-capable GPU for acceleration

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/river0098/AI-Learning-Companion-System.git
   cd AI-Learning-Companion-System
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize data directories**
   ```bash
   mkdir -p data/models data/samples logs
   ```

### Quick Start

#### Run the Main Application

```bash
cd backend/src
python main.py
```

#### Test Individual Modules

```bash
# Test vision analysis
python backend/src/vision/vision_analyzer.py

# Test OCR
python backend/src/ocr/text_recognizer.py

# Test knowledge graph
python backend/src/knowledge_graph/graph_engine.py

# Test time tracking
python backend/src/time_tracking/tracker.py

# Test AI companion
python backend/src/ai_companion/companion.py

# Test dashboard generator
python backend/src/dashboard/generator.py
```

#### Example Usage

```python
from main import AILearningCompanion

# Initialize system
system = AILearningCompanion()

# Start learning session
session = system.start_session("student_001")

# Process camera frame (simulated)
import numpy as np
frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = system.process_frame(frame)

# Student asks for help
response = system.student_message(
    "I don't understand this problem",
    mode="guide"
)
print(f"AI: {response['ai_message']}")

# Get student dashboard
dashboard = system.get_student_dashboard("student_001")
print(f"Study time today: {dashboard['today_minutes']} minutes")

# Get parent dashboard (privacy-safe)
parent_view = system.get_parent_dashboard("student_001")
print(f"Weekly summary: {parent_view['summary']}")

# End session
summary = system.end_session()
print(f"Session complete: {summary['focused_time']}s focused time")

# Cleanup
system.cleanup()
```

---

## 📁 Project Structure

```
AI-Learning-Companion-System/
├── backend/
│   ├── src/
│   │   ├── vision/              # Computer vision analysis
│   │   │   └── vision_analyzer.py
│   │   ├── ocr/                 # OCR & handwriting recognition
│   │   │   └── text_recognizer.py
│   │   ├── knowledge_graph/     # Knowledge mapping engine
│   │   │   └── graph_engine.py
│   │   ├── time_tracking/       # Time & behavior tracking
│   │   │   └── tracker.py
│   │   ├── ai_companion/        # AI chat companion
│   │   │   └── companion.py
│   │   ├── dashboard/           # Dashboard generation
│   │   │   └── generator.py
│   │   ├── storage/             # Data persistence
│   │   ├── utils/               # Utilities
│   │   └── main.py              # Main application
│   └── tests/                   # Unit tests
│
├── frontend/                    # Web interface (future)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── public/
│
├── config/
│   └── settings.yaml            # System configuration
│
├── data/
│   ├── models/                  # Pre-trained models
│   └── samples/                 # Sample data
│
├── docs/                        # Additional documentation
│
├── scripts/                     # Utility scripts
│
├── ARCHITECTURE.md              # Detailed architecture
├── README.md                    # This file
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment template
```

---

## 🔒 Privacy & Security

### Core Principles

1. **No Video Storage**: Raw camera feeds are NEVER saved
2. **Feature Extraction Only**: Only AI-extracted features are stored
3. **Local-First**: All processing happens on-device by default
4. **Encrypted Storage**: Database uses encryption at rest
5. **Anonymized Parent View**: Parents see summaries, not live feed
6. **User Control**: Students can pause/disable monitoring anytime

### Data Lifecycle

```
Camera Frame → Feature Extraction → Analysis → Storage
     ↓              ↓                  ↓          ↓
(Discarded)    (Features only)    (Insights)  (Encrypted)
```

### Compliance

- GDPR-friendly (data minimization, user control)
- COPPA-compliant (parental consent, age-appropriate)
- FERPA-aligned (educational privacy)

---

## 🎯 AI Companion Interaction Examples

### Scenario 1: Detected Distraction
```
[Student looking away for 3 minutes]

AI (Friend Mode): "You've been idle for 3 minutes. Need a short break?
                    Or maybe something is distracting you?"

Quick Replies: [Yes, take a break] [No, keep studying] [Just 5 more minutes]
```

### Scenario 2: Confusion Detection
```
[OCR detects same problem attempted multiple times, facial expression: confused]

AI (Guide Mode): "I notice you're working hard on this quadratic equation.
                   Want a hint? Think about factoring first."

Quick Replies: [Yes, explain more] [Show an example] [I'll figure it out]
```

### Scenario 3: Achievement Celebration
```
[Student completes 10 problems, maintains 45-minute focus]

AI (Coach Mode): "Wow! You just completed 10 problems with 45 minutes of
                   solid focus—that's your new record! 🎉"

Quick Replies: [Thanks!] [Set new goal] [Take a break]
```

### Scenario 4: Fatigue Detection
```
[Slouched posture, yawning detected, 90 minutes continuous study]

AI (Friend Mode): "You've been studying for 90 minutes straight. Your brain
                    needs a break! How about a 5-minute walk?"

Quick Replies: [Good idea] [Just 10 more minutes] [I'm okay]
```

---

## 📊 Dashboard Previews

### Student Dashboard Features
- ⏱️ **Time Visualization**: Daily/weekly study time charts
- 📈 **Progress Tracking**: Topic mastery radar charts
- 🏆 **Achievements**: Badges and streaks
- 💬 **AI Chat History**: Recent companion interactions
- 🎯 **Recommendations**: Personalized next steps

### Parent Dashboard Features
- 📅 **Weekly Summaries**: Aggregated study time
- 📚 **Subject Progress**: Mastery levels by topic
- 💡 **AI Insights**: "Your child shows strong progress in Math"
- 📊 **Trends**: 4-week progress visualization
- ✅ **Recommendations**: Suggestions for support

---

## 🛠️ Configuration

Edit `config/settings.yaml` to customize:

- **Privacy**: Enable/disable features, data retention
- **Camera**: Device ID, resolution, sample rate
- **Vision**: Detection thresholds, enabled features
- **OCR**: Language support, recognition engines
- **AI Companion**: Personality, intervention rules
- **Dashboards**: Update intervals, export formats

See [settings.yaml](config/settings.yaml) for all options.

---

## 🧪 Testing

```bash
# Run all tests
pytest backend/tests/

# Test specific module
pytest backend/tests/test_vision.py

# With coverage
pytest --cov=backend/src backend/tests/
```

---

## 🌐 API Documentation

(Future: REST API and WebSocket endpoints)

### Planned Endpoints

- `POST /session/start` - Start learning session
- `POST /session/end` - End session
- `POST /frame/analyze` - Analyze camera frame
- `POST /content/recognize` - OCR content
- `POST /chat/message` - Send message to AI companion
- `GET /dashboard/student` - Get student dashboard
- `GET /dashboard/parent` - Get parent dashboard
- `WS /live` - WebSocket for real-time updates

---

## 🚧 Roadmap

### Version 1.0 (Current)
- ✅ Core vision analysis
- ✅ OCR and handwriting recognition
- ✅ Knowledge graph engine
- ✅ Time tracking and behavior detection
- ✅ AI companion with 3 modes
- ✅ Student and parent dashboards

### Version 2.0 (Planned)
- 🔲 Web-based UI (React frontend)
- 🔲 REST API with FastAPI
- 🔲 Real-time WebSocket notifications
- 🔲 Voice interaction support
- 🔲 Multi-student classroom mode
- 🔲 Advanced emotion recognition

### Version 3.0 (Future)
- 🔲 Gamification and badges
- 🔲 AR overlay for desk projection
- 🔲 Integration with learning platforms
- 🔲 Mobile app for parents
- 🔲 Advanced analytics and predictions
- 🔲 Collaborative learning features

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) (coming soon) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black backend/`)
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **MediaPipe** - Computer vision framework by Google
- **PaddleOCR** - Multilingual OCR toolkit
- **NetworkX** - Graph analysis library
- **OpenCV** - Computer vision library
- Educational psychology research on learning patterns and motivation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/river0098/AI-Learning-Companion-System/issues)
- **Discussions**: [GitHub Discussions](https://github.com/river0098/AI-Learning-Companion-System/discussions)
- **Email**: support@ailearningcompanion.example.com

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

## 📖 Citation

If you use this system in research or education, please cite:

```bibtex
@software{ai_learning_companion_2025,
  title = {AI Learning Companion System},
  author = {AI Learning Companion Team},
  year = {2025},
  url = {https://github.com/river0098/AI-Learning-Companion-System}
}
```

---

**Built with ❤️ for students, by educators and AI researchers**

*Transform supervision into companionship. Empower learning with empathy.*
