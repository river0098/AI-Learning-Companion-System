# 🚀 Quick Start Guide - AI Learning Companion System

## 5-Minute Demo

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Run the Demo

```bash
cd backend/src
python main.py
```

You should see output like:

```
============================================================
AI LEARNING COMPANION SYSTEM
Transform supervision into intelligent companionship
============================================================

🚀 Initializing AI Learning Companion System...
✅ System initialized successfully!

✓ Session started: session_student_demo_001_1234567890.0

📊 System is now monitoring and analyzing...
   - Vision: Detecting posture, gaze, emotion
   - OCR: Ready to recognize content
   - AI Companion: Monitoring for interventions
   - Time Tracker: Recording learning patterns

💬 Student message: 'I don't understand this problem'
🤖 AI Companion (guide): I'm here to help! What specifically about this is confusing?

📊 Generating dashboards...
   Student: 0 day streak, 0 achievements
   Parent: low engagement, 0.5% productivity

✓ Session ended: 0s focused time

✅ System cleaned up successfully

============================================================
System demonstration complete!
============================================================
```

### Step 3: Test Individual Modules

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

# Test dashboard
python backend/src/dashboard/generator.py
```

Each module has a `if __name__ == "__main__"` block with example usage.

---

## Quick Integration Example

```python
from main import AILearningCompanion
import numpy as np

# Initialize
companion = AILearningCompanion()

# Start session
session = companion.start_session("student_001")
print(f"Started: {session['session_id']}")

# Simulate camera frame
frame = np.zeros((480, 640, 3), dtype=np.uint8)
result = companion.process_frame(frame)

# Student interaction
response = companion.student_message(
    "I'm stuck on this problem",
    mode="guide"
)
print(f"AI: {response['ai_message']}")

# Record exercise
companion.record_exercise_result(
    concept_id="math_arithmetic_addition",
    correct=True,
    time_spent=120
)

# Get dashboards
student_dash = companion.get_student_dashboard("student_001")
parent_dash = companion.get_parent_dashboard("student_001")

# End session
summary = companion.end_session()
print(f"Focused: {summary['focused_time']}s")

# Cleanup
companion.cleanup()
```

---

## Configuration

Edit `config/settings.yaml` to customize behavior:

```yaml
# Key settings
camera:
  sample_interval: 3  # seconds between frame analysis

vision:
  enable_emotion_recognition: true
  confidence_threshold: 0.5

ai_companion:
  personality: "encouraging"  # encouraging, strict, playful
  default_mode: "coach"  # guide, coach, friend

privacy:
  save_raw_images: false  # ALWAYS false for privacy
```

---

## Next Steps

1. **Connect Real Camera**: Modify `main.py` to use actual camera
2. **Add OCR Integration**: Install PaddleOCR or Google Vision API
3. **Build Web UI**: Create React frontend (coming soon)
4. **Deploy**: Set up on edge device (Raspberry Pi, Jetson Nano)

---

## Troubleshooting

### MediaPipe Installation Issues

```bash
pip install mediapipe --upgrade
```

### OpenCV Camera Access

```bash
# Linux: Add user to video group
sudo usermod -a -G video $USER

# Test camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### PaddleOCR Setup

```bash
pip install paddlepaddle paddleocr

# Test OCR
python -c "from paddleocr import PaddleOCR; print('OK')"
```

---

## Demo Scenarios

### Scenario 1: Homework Helper

```python
# Student working on math homework
companion.start_session("alice")

# Detect confusion after 5 minutes on same problem
# AI intervenes: "Want a hint about this equation?"

# Student accepts help
response = companion.student_message("Yes please", mode="guide")
# AI: "Think about isolating the variable first..."
```

### Scenario 2: Focus Coach

```python
# Track 25-minute focus session
# After 25 min, AI suggests: "Great focus! Take a 5-min break?"

# Track productivity over days
dashboard = companion.get_student_dashboard("alice")
print(f"Streak: {dashboard['streak']} days")
```

### Scenario 3: Parent Insights

```python
# Parent checks weekly progress (no live feed)
parent_view = companion.get_parent_dashboard("alice")
print(parent_view['summary'])
# "This week, your child studied for 180 minutes.
#  They're showing strong progress in Math."
```

---

**Ready to transform learning? Start experimenting!** 🎓✨
