"""
Time Tracking & Behavior Detection Module
Tracks learning states, session duration, and behavioral patterns.
Detects: Active study, Idle time, Distractions, Fatigue.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json


class LearningState(Enum):
    """Learning states based on detected behavior"""
    ACTIVE = "active"  # Focused studying
    IDLE = "idle"  # No activity detected
    DISTRACTED = "distracted"  # Looking away, no pen movement
    BREAK = "break"  # Intentional break
    FATIGUED = "fatigued"  # Signs of tiredness
    OFFLINE = "offline"  # Student not at desk


@dataclass
class StateTransition:
    """Record of state change"""
    timestamp: datetime
    from_state: LearningState
    to_state: LearningState
    trigger: str  # What caused the transition
    duration_in_previous_state: int  # seconds


@dataclass
class StudySession:
    """Complete study session record"""
    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_time: int  # seconds
    focused_time: int  # seconds in ACTIVE state
    idle_time: int  # seconds in IDLE state
    break_time: int  # seconds in BREAK state
    distraction_count: int
    state_transitions: List[StateTransition]
    detected_topics: List[str]
    current_state: LearningState


@dataclass
class ProductivityMetrics:
    """Aggregated productivity statistics"""
    date: datetime
    total_sessions: int
    total_study_time: int  # seconds
    effective_study_time: int  # Active state time
    productivity_ratio: float  # effective / total
    average_focus_duration: int  # Average continuous active time
    longest_focus_streak: int  # Longest active period
    distraction_rate: float  # Distractions per hour
    peak_productivity_hour: Optional[int]  # Hour of day (0-23)


class TimeTracker:
    """
    Tracks learning time and behavioral patterns.
    Maintains state machine for learning states.
    """

    def __init__(self):
        """Initialize time tracker"""
        self.sessions: Dict[str, StudySession] = {}
        self.current_sessions: Dict[str, str] = {}  # student_id -> session_id
        self.state_history: Dict[str, List[StateTransition]] = {}

        # State transition rules
        self.idle_threshold = 120  # seconds before marking as idle
        self.distraction_threshold = 90  # seconds looking away
        self.fatigue_threshold = 5400  # 90 minutes continuous study

    def start_session(self, student_id: str) -> StudySession:
        """
        Start a new study session.

        Args:
            student_id: Student identifier

        Returns:
            Created StudySession object
        """
        session_id = f"session_{student_id}_{datetime.now().timestamp()}"

        session = StudySession(
            session_id=session_id,
            student_id=student_id,
            start_time=datetime.now(),
            end_time=None,
            total_time=0,
            focused_time=0,
            idle_time=0,
            break_time=0,
            distraction_count=0,
            state_transitions=[],
            detected_topics=[],
            current_state=LearningState.ACTIVE
        )

        self.sessions[session_id] = session
        self.current_sessions[student_id] = session_id

        return session

    def end_session(self, student_id: str) -> Optional[StudySession]:
        """
        End the current study session.

        Args:
            student_id: Student identifier

        Returns:
            Completed StudySession object
        """
        if student_id not in self.current_sessions:
            return None

        session_id = self.current_sessions[student_id]
        session = self.sessions[session_id]

        session.end_time = datetime.now()
        session.total_time = int((session.end_time - session.start_time).total_seconds())

        # Remove from current sessions
        del self.current_sessions[student_id]

        return session

    def update_state(self,
                    student_id: str,
                    vision_features: Dict,
                    ocr_activity: bool = False) -> StateTransition:
        """
        Update learning state based on detected behavior.

        Args:
            student_id: Student identifier
            vision_features: Output from VisionAnalyzer
            ocr_activity: Whether new content was detected

        Returns:
            StateTransition if state changed, None otherwise
        """
        if student_id not in self.current_sessions:
            return None

        session_id = self.current_sessions[student_id]
        session = self.sessions[session_id]

        # Get current state and determine new state
        old_state = session.current_state
        new_state = self._determine_state(vision_features, ocr_activity, session)

        # Check for state transition
        if new_state != old_state:
            transition = self._create_transition(session, old_state, new_state)
            session.state_transitions.append(transition)

            # Update session metrics
            self._update_session_metrics(session, transition)

            # Update current state
            session.current_state = new_state

            return transition

        return None

    def _determine_state(self,
                        vision_features: Dict,
                        ocr_activity: bool,
                        session: StudySession) -> LearningState:
        """
        Determine learning state from vision and activity data.

        State transition logic:
        - ACTIVE: Hand/pen detected, gaze on desk, posture good
        - IDLE: No movement for >2 minutes
        - DISTRACTED: Gaze away, no pen activity
        - FATIGUED: Slouched posture, rubbing eyes, >90min continuous
        - BREAK: Intentional break (triggered by user or system suggestion)
        """
        # Extract features
        posture = vision_features.get("posture", "unknown")
        gaze = vision_features.get("gaze_direction", "unknown")
        activity_level = vision_features.get("activity_level", 0.0)
        emotion = vision_features.get("emotion", "neutral")
        hand_detected = vision_features.get("hand_detected", False)
        pen_activity = vision_features.get("pen_activity", False)

        # Calculate time in current state
        if session.state_transitions:
            last_transition = session.state_transitions[-1]
            time_in_state = (datetime.now() - last_transition.timestamp).total_seconds()
        else:
            time_in_state = (datetime.now() - session.start_time).total_seconds()

        # Check for fatigue
        if (emotion == "tired" or
            (posture == "slouched" and time_in_state > self.fatigue_threshold)):
            return LearningState.FATIGUED

        # Check for intentional break
        if session.current_state == LearningState.BREAK:
            # Stay in break unless activity resumes
            if hand_detected and activity_level > 0.3:
                return LearningState.ACTIVE
            return LearningState.BREAK

        # Check for active studying
        if (hand_detected and
            pen_activity and
            gaze in ["desk", "screen"] and
            activity_level > 0.2):
            return LearningState.ACTIVE

        # Check for distraction
        if gaze == "away" and time_in_state > self.distraction_threshold:
            return LearningState.DISTRACTED

        # Check for idle
        if activity_level < 0.1 and time_in_state > self.idle_threshold:
            return LearningState.IDLE

        # Default to current state if no clear transition
        return session.current_state

    def _create_transition(self,
                          session: StudySession,
                          old_state: LearningState,
                          new_state: LearningState) -> StateTransition:
        """Create state transition record"""
        if session.state_transitions:
            last_transition_time = session.state_transitions[-1].timestamp
        else:
            last_transition_time = session.start_time

        duration = int((datetime.now() - last_transition_time).total_seconds())

        # Determine trigger
        trigger = self._determine_trigger(old_state, new_state)

        return StateTransition(
            timestamp=datetime.now(),
            from_state=old_state,
            to_state=new_state,
            trigger=trigger,
            duration_in_previous_state=duration
        )

    def _determine_trigger(self,
                          old_state: LearningState,
                          new_state: LearningState) -> str:
        """Determine what triggered the state change"""
        if new_state == LearningState.ACTIVE:
            return "resumed_activity"
        elif new_state == LearningState.IDLE:
            return "no_activity_detected"
        elif new_state == LearningState.DISTRACTED:
            return "gaze_away"
        elif new_state == LearningState.FATIGUED:
            return "fatigue_detected"
        elif new_state == LearningState.BREAK:
            return "break_started"
        else:
            return "unknown"

    def _update_session_metrics(self,
                               session: StudySession,
                               transition: StateTransition):
        """Update session time metrics based on state transition"""
        duration = transition.duration_in_previous_state

        if transition.from_state == LearningState.ACTIVE:
            session.focused_time += duration
        elif transition.from_state == LearningState.IDLE:
            session.idle_time += duration
        elif transition.from_state == LearningState.BREAK:
            session.break_time += duration
        elif transition.from_state == LearningState.DISTRACTED:
            session.distraction_count += 1

    def get_session(self, session_id: str) -> Optional[StudySession]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_current_session(self, student_id: str) -> Optional[StudySession]:
        """Get student's current active session"""
        if student_id in self.current_sessions:
            session_id = self.current_sessions[student_id]
            return self.sessions[session_id]
        return None

    def calculate_productivity_metrics(self,
                                       student_id: str,
                                       date: datetime) -> ProductivityMetrics:
        """
        Calculate productivity metrics for a specific date.

        Args:
            student_id: Student identifier
            date: Date to analyze

        Returns:
            ProductivityMetrics object
        """
        # Filter sessions for the given date
        date_sessions = [
            session for session in self.sessions.values()
            if (session.student_id == student_id and
                session.start_time.date() == date.date())
        ]

        if not date_sessions:
            return ProductivityMetrics(
                date=date,
                total_sessions=0,
                total_study_time=0,
                effective_study_time=0,
                productivity_ratio=0.0,
                average_focus_duration=0,
                longest_focus_streak=0,
                distraction_rate=0.0,
                peak_productivity_hour=None
            )

        # Aggregate metrics
        total_time = sum(s.total_time for s in date_sessions)
        focused_time = sum(s.focused_time for s in date_sessions)

        productivity_ratio = focused_time / total_time if total_time > 0 else 0.0

        # Calculate focus durations
        focus_durations = []
        for session in date_sessions:
            current_duration = 0
            for transition in session.state_transitions:
                if transition.from_state == LearningState.ACTIVE:
                    current_duration = transition.duration_in_previous_state
                    focus_durations.append(current_duration)

        avg_focus = sum(focus_durations) / len(focus_durations) if focus_durations else 0
        longest_focus = max(focus_durations) if focus_durations else 0

        # Calculate distraction rate (per hour)
        total_distractions = sum(s.distraction_count for s in date_sessions)
        distraction_rate = (total_distractions / (total_time / 3600)) if total_time > 0 else 0

        # Find peak productivity hour
        hour_productivity = self._calculate_hourly_productivity(date_sessions)
        peak_hour = max(hour_productivity, key=hour_productivity.get) if hour_productivity else None

        return ProductivityMetrics(
            date=date,
            total_sessions=len(date_sessions),
            total_study_time=total_time,
            effective_study_time=focused_time,
            productivity_ratio=productivity_ratio,
            average_focus_duration=int(avg_focus),
            longest_focus_streak=longest_focus,
            distraction_rate=distraction_rate,
            peak_productivity_hour=peak_hour
        )

    def _calculate_hourly_productivity(self,
                                      sessions: List[StudySession]) -> Dict[int, int]:
        """Calculate focused time by hour of day"""
        hourly = {}

        for session in sessions:
            hour = session.start_time.hour
            hourly[hour] = hourly.get(hour, 0) + session.focused_time

        return hourly

    def get_learning_patterns(self, student_id: str, days: int = 7) -> Dict:
        """
        Analyze learning patterns over recent days.

        Returns:
            Dictionary with pattern insights
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_sessions = [
            s for s in self.sessions.values()
            if (s.student_id == student_id and
                s.start_time >= cutoff_date)
        ]

        if not recent_sessions:
            return {"pattern": "insufficient_data"}

        # Analyze patterns
        total_focused = sum(s.focused_time for s in recent_sessions)
        avg_daily_time = total_focused / days / 60  # minutes per day

        # Identify best time of day
        hour_counts = {}
        for session in recent_sessions:
            hour = session.start_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        most_common_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None

        # Calculate consistency (standard deviation of daily times)
        # TODO: Implement consistency calculation

        return {
            "days_analyzed": days,
            "total_sessions": len(recent_sessions),
            "avg_daily_minutes": round(avg_daily_time, 1),
            "most_productive_hour": most_common_hour,
            "total_focused_hours": round(total_focused / 3600, 1)
        }


# Example usage
if __name__ == "__main__":
    print("Time Tracking & Behavior Detection - Test Mode")
    print("=" * 50)

    tracker = TimeTracker()
    student_id = "student_001"

    # Start session
    print("\n⏱️  Starting study session...")
    session = tracker.start_session(student_id)
    print(f"Session ID: {session.session_id}")

    # Simulate state transitions
    print("\n📊 Simulating behavior detection...")

    # Active studying
    vision_data_active = {
        "posture": "upright",
        "gaze_direction": "desk",
        "activity_level": 0.7,
        "emotion": "focused",
        "hand_detected": True,
        "pen_activity": True
    }

    transition = tracker.update_state(student_id, vision_data_active)
    if transition:
        print(f"State: {transition.to_state.value}")

    # Simulate idle
    vision_data_idle = {
        "posture": "upright",
        "gaze_direction": "away",
        "activity_level": 0.0,
        "emotion": "neutral",
        "hand_detected": False,
        "pen_activity": False
    }

    # Get current session
    current = tracker.get_current_session(student_id)
    print(f"\n📈 Current Session Stats:")
    print(f"  - State: {current.current_state.value}")
    print(f"  - Focused time: {current.focused_time}s")
    print(f"  - Idle time: {current.idle_time}s")
    print(f"  - Distractions: {current.distraction_count}")

    # Calculate metrics
    metrics = tracker.calculate_productivity_metrics(student_id, datetime.now())
    print(f"\n📊 Productivity Metrics:")
    print(f"  - Total sessions: {metrics.total_sessions}")
    print(f"  - Productivity ratio: {metrics.productivity_ratio:.1%}")

    print("\n✓ Time tracking system operational")
