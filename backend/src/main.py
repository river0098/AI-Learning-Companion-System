"""
AI Learning Companion System - Main Application
Coordinates all modules and provides unified API.
"""

import cv2
import numpy as np
from typing import Dict, Optional
from datetime import datetime

from vision.vision_analyzer import VisionAnalyzer, FrameSampler, VisionFeatures
from ocr.text_recognizer import TextRecognizer, RecognizedText
from knowledge_graph.graph_engine import KnowledgeGraphEngine
from time_tracking.tracker import TimeTracker, LearningState
from ai_companion.companion import AICompanion, CompanionMode, ConversationContext
from dashboard.generator import DashboardGenerator


class AILearningCompanion:
    """
    Main application class that coordinates all modules.
    Provides a unified interface for the AI Learning Companion System.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the AI Learning Companion System.

        Args:
            config: Configuration dictionary (optional)
        """
        self.config = config or self._default_config()

        # Initialize all modules
        print("🚀 Initializing AI Learning Companion System...")

        self.vision_analyzer = VisionAnalyzer(
            enable_pose=True,
            enable_face=True,
            enable_hands=True
        )

        self.frame_sampler = FrameSampler(
            base_interval=self.config.get("frame_sample_interval", 3)
        )

        self.text_recognizer = TextRecognizer(
            use_gpu=self.config.get("use_gpu", False),
            enable_math=True
        )

        self.knowledge_graph = KnowledgeGraphEngine()

        self.time_tracker = TimeTracker()

        self.ai_companion = AICompanion(
            personality=self.config.get("companion_personality", "encouraging"),
            default_mode=CompanionMode.COACH
        )

        self.dashboard_generator = DashboardGenerator(
            knowledge_graph=self.knowledge_graph,
            time_tracker=self.time_tracker,
            ai_companion=self.ai_companion
        )

        # Current student session
        self.current_student: Optional[str] = None
        self.camera = None

        print("✅ System initialized successfully!")

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "frame_sample_interval": 3,  # seconds
            "use_gpu": False,
            "companion_personality": "encouraging",
            "privacy_mode": True,
            "save_features": True,
            "save_raw_images": False
        }

    def start_session(self, student_id: str) -> Dict:
        """
        Start a learning session for a student.

        Args:
            student_id: Student identifier

        Returns:
            Session information
        """
        print(f"\n📚 Starting session for student: {student_id}")

        self.current_student = student_id

        # Start time tracking
        session = self.time_tracker.start_session(student_id)

        # Initialize camera (in production)
        # self.camera = cv2.VideoCapture(0)

        return {
            "session_id": session.session_id,
            "start_time": session.start_time.isoformat(),
            "status": "active"
        }

    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single camera frame.

        Args:
            frame: Camera frame (BGR format)

        Returns:
            Processing results
        """
        if not self.current_student:
            return {"error": "No active session"}

        current_time = datetime.now()

        # Check if frame should be sampled
        if not self.frame_sampler.should_sample(current_time):
            return {"sampled": False}

        # Analyze vision
        vision_features = self.vision_analyzer.analyze_frame(frame)

        # Update learning state
        transition = self.time_tracker.update_state(
            self.current_student,
            vision_features.__dict__,
            ocr_activity=False
        )

        # Check for AI intervention
        context = self._build_context()
        intervention = self.ai_companion.evaluate_intervention(context)

        # Build response
        result = {
            "sampled": True,
            "timestamp": current_time.isoformat(),
            "vision": {
                "posture": vision_features.posture,
                "gaze": vision_features.gaze_direction,
                "activity": vision_features.activity_level,
                "emotion": vision_features.emotion
            },
            "state": transition.to_state.value if transition else None,
            "ai_message": intervention.message if intervention else None
        }

        return result

    def process_content(self, image: np.ndarray) -> Dict:
        """
        Process learning content (OCR on notebook/textbook).

        Args:
            image: Image of learning material

        Returns:
            OCR and analysis results
        """
        if not self.current_student:
            return {"error": "No active session"}

        # Recognize text
        text_result = self.text_recognizer.recognize_text(image)

        # Update knowledge graph
        if text_result.detected_topics:
            # Map topics to concepts
            concepts = self.knowledge_graph.find_concepts_by_topic(
                text_result.detected_topics
            )

            # Update session topics
            session = self.time_tracker.get_current_session(self.current_student)
            if session:
                session.detected_topics = list(set(
                    session.detected_topics + text_result.detected_topics
                ))

        return {
            "text": text_result.text,
            "topics": text_result.detected_topics,
            "language": text_result.language,
            "confidence": text_result.confidence
        }

    def record_exercise_result(self,
                               concept_id: str,
                               correct: bool,
                               time_spent: int) -> Dict:
        """
        Record exercise completion and update mastery.

        Args:
            concept_id: Concept being practiced
            correct: Whether answer was correct
            time_spent: Time spent in seconds

        Returns:
            Updated mastery information
        """
        if not self.current_student:
            return {"error": "No active session"}

        self.knowledge_graph.update_mastery(
            self.current_student,
            concept_id,
            {
                "correct": correct,
                "time_spent": time_spent
            }
        )

        mastery = self.knowledge_graph.get_mastery_level(
            self.current_student,
            concept_id
        )

        return {
            "concept_id": concept_id,
            "new_mastery": mastery,
            "mastery_percent": f"{mastery:.1%}"
        }

    def student_message(self, message: str, mode: Optional[str] = None) -> Dict:
        """
        Handle student's chat message to AI companion.

        Args:
            message: Student's message
            mode: Optional mode ("guide", "coach", "friend")

        Returns:
            AI response
        """
        if not self.current_student:
            return {"error": "No active session"}

        # Convert mode string to enum
        companion_mode = None
        if mode:
            companion_mode = CompanionMode(mode)

        # Generate response
        context = self._build_context()
        response = self.ai_companion.generate_response(
            message,
            context,
            mode=companion_mode
        )

        return {
            "ai_message": response.message,
            "mode": response.mode.value,
            "requires_response": response.requires_response,
            "suggested_responses": response.suggested_responses
        }

    def end_session(self) -> Dict:
        """
        End the current learning session.

        Returns:
            Session summary
        """
        if not self.current_student:
            return {"error": "No active session"}

        # End time tracking
        session = self.time_tracker.end_session(self.current_student)

        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None

        # Generate summary
        summary = {
            "session_id": session.session_id,
            "duration": session.total_time,
            "focused_time": session.focused_time,
            "productivity": session.focused_time / session.total_time if session.total_time > 0 else 0,
            "topics_studied": session.detected_topics,
            "distractions": session.distraction_count
        }

        self.current_student = None

        return summary

    def get_student_dashboard(self, student_id: str) -> Dict:
        """
        Generate student dashboard.

        Args:
            student_id: Student identifier

        Returns:
            Dashboard data
        """
        dashboard = self.dashboard_generator.generate_student_dashboard(student_id)

        return {
            "today_minutes": dashboard.today_study_time // 60,
            "week_minutes": dashboard.week_study_time // 60,
            "streak": dashboard.current_streak,
            "topics_mastered": len(dashboard.topics_mastered),
            "achievements": dashboard.recent_achievements,
            "productivity": dashboard.productivity_trend,
            "recommendations": dashboard.recommended_topics
        }

    def get_parent_dashboard(self, student_id: str) -> Dict:
        """
        Generate parent dashboard (privacy-safe).

        Args:
            student_id: Student identifier

        Returns:
            Anonymized dashboard data
        """
        dashboard = self.dashboard_generator.generate_parent_dashboard(student_id)

        return {
            "week_minutes": dashboard.week_total_time // 60,
            "month_minutes": dashboard.month_total_time // 60,
            "subjects": dashboard.subjects_progress,
            "productivity_score": dashboard.productivity_score,
            "engagement": dashboard.engagement_level,
            "summary": dashboard.weekly_summary,
            "recommendations": dashboard.recommendations_for_parent
        }

    def _build_context(self) -> ConversationContext:
        """Build conversation context for AI companion"""
        if not self.current_student:
            return None

        session = self.time_tracker.get_current_session(self.current_student)
        knowledge_map = self.knowledge_graph.get_student_knowledge_map(self.current_student)

        if not session:
            # Create empty context
            return ConversationContext(
                student_id=self.current_student,
                current_state="offline",
                time_in_state=0,
                recent_topics=[],
                mastery_levels={},
                session_duration=0,
                productivity_ratio=0.0,
                recent_achievements=[],
                detected_emotion="neutral",
                last_intervention_time=None
            )

        # Calculate time in current state
        if session.state_transitions:
            last_transition = session.state_transitions[-1]
            time_in_state = int((datetime.now() - last_transition.timestamp).total_seconds())
        else:
            time_in_state = int((datetime.now() - session.start_time).total_seconds())

        return ConversationContext(
            student_id=self.current_student,
            current_state=session.current_state.value,
            time_in_state=time_in_state,
            recent_topics=session.detected_topics,
            mastery_levels={k: v["mastery_level"] for k, v in knowledge_map.items()},
            session_duration=int((datetime.now() - session.start_time).total_seconds()),
            productivity_ratio=session.focused_time / session.total_time if session.total_time > 0 else 0,
            recent_achievements=[],  # TODO: Get from achievements tracker
            detected_emotion="neutral",  # TODO: Get from latest vision analysis
            last_intervention_time=None
        )

    def cleanup(self):
        """Cleanup resources"""
        if self.camera:
            self.camera.release()
        self.vision_analyzer.cleanup()
        print("✅ System cleaned up successfully")


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("AI LEARNING COMPANION SYSTEM")
    print("Transform supervision into intelligent companionship")
    print("=" * 60)

    # Initialize system
    system = AILearningCompanion()

    # Start session
    student_id = "student_demo_001"
    session_info = system.start_session(student_id)
    print(f"\n✓ Session started: {session_info['session_id']}")

    # Simulate processing
    print("\n📊 System is now monitoring and analyzing...")
    print("   - Vision: Detecting posture, gaze, emotion")
    print("   - OCR: Ready to recognize content")
    print("   - AI Companion: Monitoring for interventions")
    print("   - Time Tracker: Recording learning patterns")

    # Simulate student interaction
    print("\n💬 Student message: 'I don't understand this problem'")
    response = system.student_message("I don't understand this problem", mode="guide")
    print(f"🤖 AI Companion ({response['mode']}): {response['ai_message']}")

    # Get dashboard
    print("\n📊 Generating dashboards...")
    student_dash = system.get_student_dashboard(student_id)
    print(f"   Student: {student_dash['streak']} day streak, {len(student_dash['achievements'])} achievements")

    parent_dash = system.get_parent_dashboard(student_id)
    print(f"   Parent: {parent_dash['engagement']} engagement, {parent_dash['productivity_score']:.1%} productivity")

    # End session
    summary = system.end_session()
    print(f"\n✓ Session ended: {summary['focused_time']}s focused time")

    # Cleanup
    system.cleanup()

    print("\n" + "=" * 60)
    print("System demonstration complete!")
    print("=" * 60)
