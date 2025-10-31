"""
Dashboard Generator
Creates student and parent dashboards with visualizations and insights.
Privacy-safe: parent view shows only aggregated, anonymized data.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json


@dataclass
class DashboardData:
    """Base dashboard data structure"""
    generated_at: datetime
    student_id: str
    dashboard_type: str  # "student" or "parent"


@dataclass
class StudentDashboard(DashboardData):
    """Student-facing dashboard with detailed information"""
    # Time metrics
    today_study_time: int  # seconds
    week_study_time: int
    month_study_time: int
    current_streak: int  # consecutive days

    # Progress metrics
    topics_mastered: List[Dict]  # List of {topic, mastery_level}
    recent_achievements: List[str]
    learning_path_progress: float  # 0.0 to 1.0

    # Session data
    recent_sessions: List[Dict]
    average_focus_duration: int  # seconds
    productivity_trend: List[float]  # Last 7 days

    # AI companion
    ai_interactions_count: int
    helpful_hints_received: int

    # Recommendations
    recommended_topics: List[str]
    suggested_next_session: Dict  # {duration, topics, difficulty}


@dataclass
class ParentDashboard(DashboardData):
    """Parent-facing dashboard with anonymized summaries"""
    # Time summaries (aggregated)
    week_total_time: int  # seconds
    week_average_daily: int
    month_total_time: int

    # Progress summaries
    subjects_progress: Dict[str, float]  # subject -> mastery %
    improvement_areas: List[str]
    strengths: List[str]

    # Behavioral insights (anonymized)
    productivity_score: float  # 0.0 to 1.0
    consistency_score: float  # 0.0 to 1.0
    engagement_level: str  # "high", "medium", "low"

    # AI-generated insights
    weekly_summary: str
    recommendations_for_parent: List[str]

    # Trends (no live surveillance)
    study_time_trend: List[int]  # Last 4 weeks
    progress_trend: List[float]  # Overall mastery trend


class DashboardGenerator:
    """
    Generates student and parent dashboards from learning data.
    Ensures parent dashboard respects privacy boundaries.
    """

    def __init__(self,
                 knowledge_graph=None,
                 time_tracker=None,
                 ai_companion=None):
        """
        Initialize dashboard generator.

        Args:
            knowledge_graph: KnowledgeGraphEngine instance
            time_tracker: TimeTracker instance
            ai_companion: AICompanion instance
        """
        self.knowledge_graph = knowledge_graph
        self.time_tracker = time_tracker
        self.ai_companion = ai_companion

    def generate_student_dashboard(self, student_id: str) -> StudentDashboard:
        """
        Generate comprehensive student dashboard.

        Args:
            student_id: Student identifier

        Returns:
            StudentDashboard object
        """
        now = datetime.now()

        # Calculate time metrics
        today_time = self._calculate_study_time(student_id, days=1)
        week_time = self._calculate_study_time(student_id, days=7)
        month_time = self._calculate_study_time(student_id, days=30)
        streak = self._calculate_streak(student_id)

        # Get knowledge progress
        knowledge_map = (self.knowledge_graph.get_student_knowledge_map(student_id)
                        if self.knowledge_graph else {})

        topics_mastered = [
            {
                "topic": topic_id,
                "mastery": state["mastery_level"],
                "last_practiced": state["last_practiced"]
            }
            for topic_id, state in knowledge_map.items()
            if state["mastery_level"] >= 0.7
        ]

        # Get achievements
        achievements = self._get_recent_achievements(student_id)

        # Get recent sessions
        recent_sessions = self._get_recent_sessions(student_id, limit=5)

        # Calculate productivity trend
        productivity_trend = self._calculate_productivity_trend(student_id, days=7)

        # Get AI interaction stats
        ai_stats = self._get_ai_interaction_stats(student_id)

        # Generate recommendations
        recommendations = self._generate_student_recommendations(student_id)

        return StudentDashboard(
            generated_at=now,
            student_id=student_id,
            dashboard_type="student",
            today_study_time=today_time,
            week_study_time=week_time,
            month_study_time=month_time,
            current_streak=streak,
            topics_mastered=topics_mastered,
            recent_achievements=achievements,
            learning_path_progress=self._calculate_path_progress(student_id),
            recent_sessions=recent_sessions,
            average_focus_duration=self._calculate_avg_focus(student_id),
            productivity_trend=productivity_trend,
            ai_interactions_count=ai_stats["interactions"],
            helpful_hints_received=ai_stats["hints"],
            recommended_topics=recommendations["topics"],
            suggested_next_session=recommendations["next_session"]
        )

    def generate_parent_dashboard(self, student_id: str) -> ParentDashboard:
        """
        Generate privacy-safe parent dashboard.
        Shows aggregated data and insights, no live surveillance.

        Args:
            student_id: Student identifier

        Returns:
            ParentDashboard object
        """
        now = datetime.now()

        # Aggregated time data (no timestamps)
        week_time = self._calculate_study_time(student_id, days=7)
        month_time = self._calculate_study_time(student_id, days=30)
        week_avg = week_time // 7

        # Progress by subject (aggregated)
        subjects_progress = self._calculate_subject_progress(student_id)

        # Identify strengths and areas for improvement
        strengths = self._identify_strengths(student_id)
        improvement_areas = self._identify_improvement_areas(student_id)

        # Calculate scores
        productivity_score = self._calculate_productivity_score(student_id)
        consistency_score = self._calculate_consistency_score(student_id)
        engagement_level = self._classify_engagement(productivity_score, consistency_score)

        # Generate AI insights
        weekly_summary = self._generate_weekly_summary(student_id)
        parent_recommendations = self._generate_parent_recommendations(student_id)

        # Calculate trends (aggregated by week)
        study_time_trend = self._calculate_weekly_trend(student_id, weeks=4)
        progress_trend = self._calculate_progress_trend(student_id, weeks=4)

        return ParentDashboard(
            generated_at=now,
            student_id=student_id,
            dashboard_type="parent",
            week_total_time=week_time,
            week_average_daily=week_avg,
            month_total_time=month_time,
            subjects_progress=subjects_progress,
            improvement_areas=improvement_areas,
            strengths=strengths,
            productivity_score=productivity_score,
            consistency_score=consistency_score,
            engagement_level=engagement_level,
            weekly_summary=weekly_summary,
            recommendations_for_parent=parent_recommendations,
            study_time_trend=study_time_trend,
            progress_trend=progress_trend
        )

    def _calculate_study_time(self, student_id: str, days: int) -> int:
        """Calculate total study time for past N days"""
        if not self.time_tracker:
            return 0

        cutoff = datetime.now() - timedelta(days=days)
        total_time = 0

        for session in self.time_tracker.sessions.values():
            if (session.student_id == student_id and
                session.start_time >= cutoff):
                total_time += session.focused_time

        return total_time

    def _calculate_streak(self, student_id: str) -> int:
        """Calculate consecutive days of study"""
        if not self.time_tracker:
            return 0

        # Get all session dates
        session_dates = set()
        for session in self.time_tracker.sessions.values():
            if session.student_id == student_id and session.focused_time > 300:  # At least 5 min
                session_dates.add(session.start_time.date())

        if not session_dates:
            return 0

        # Count consecutive days from today
        current_date = datetime.now().date()
        streak = 0

        while current_date in session_dates:
            streak += 1
            current_date -= timedelta(days=1)

        return streak

    def _get_recent_achievements(self, student_id: str) -> List[str]:
        """Get recent achievements"""
        # In production, maintain achievements database
        achievements = []

        # Check for milestones
        week_time = self._calculate_study_time(student_id, days=7)
        if week_time > 7200:  # 2 hours
            achievements.append("2+ hours this week")

        streak = self._calculate_streak(student_id)
        if streak >= 7:
            achievements.append(f"{streak}-day streak!")

        return achievements

    def _get_recent_sessions(self, student_id: str, limit: int) -> List[Dict]:
        """Get recent study sessions"""
        if not self.time_tracker:
            return []

        sessions = [
            {
                "date": s.start_time.isoformat(),
                "duration": s.total_time,
                "focused_time": s.focused_time,
                "topics": s.detected_topics
            }
            for s in sorted(
                self.time_tracker.sessions.values(),
                key=lambda x: x.start_time,
                reverse=True
            )[:limit]
            if s.student_id == student_id
        ]

        return sessions

    def _calculate_productivity_trend(self, student_id: str, days: int) -> List[float]:
        """Calculate productivity ratio for each of past N days"""
        trend = []

        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            metrics = (self.time_tracker.calculate_productivity_metrics(student_id, date)
                      if self.time_tracker else None)

            if metrics:
                trend.append(metrics.productivity_ratio)
            else:
                trend.append(0.0)

        return list(reversed(trend))

    def _get_ai_interaction_stats(self, student_id: str) -> Dict:
        """Get AI companion interaction statistics"""
        if not self.ai_companion:
            return {"interactions": 0, "hints": 0}

        interactions = len(self.ai_companion.conversation_history)
        hints = sum(
            1 for msg in self.ai_companion.conversation_history
            if msg.intent == "hint"
        )

        return {"interactions": interactions, "hints": hints}

    def _generate_student_recommendations(self, student_id: str) -> Dict:
        """Generate personalized recommendations for student"""
        recommendations = {
            "topics": [],
            "next_session": {
                "duration": 30,
                "topics": [],
                "difficulty": "medium"
            }
        }

        if self.knowledge_graph:
            # Suggest next concept to learn
            next_concept_id = self.knowledge_graph.suggest_next_concept(student_id)
            if next_concept_id:
                concept = self.knowledge_graph.get_concept(next_concept_id)
                recommendations["topics"].append(concept.name)
                recommendations["next_session"]["topics"].append(concept.name)
                recommendations["next_session"]["difficulty"] = concept.difficulty

            # Identify weak areas to review
            weak_areas = self.knowledge_graph.get_weak_areas(student_id)
            for area_id in weak_areas[:2]:
                concept = self.knowledge_graph.get_concept(area_id)
                recommendations["topics"].append(f"Review: {concept.name}")

        return recommendations

    def _calculate_path_progress(self, student_id: str) -> float:
        """Calculate progress on current learning path"""
        # Simplified - in production, track active learning paths
        if not self.knowledge_graph:
            return 0.0

        knowledge_map = self.knowledge_graph.get_student_knowledge_map(student_id)
        if not knowledge_map:
            return 0.0

        avg_mastery = sum(s["mastery_level"] for s in knowledge_map.values()) / len(knowledge_map)
        return avg_mastery

    def _calculate_avg_focus(self, student_id: str) -> int:
        """Calculate average focus duration"""
        if not self.time_tracker:
            return 0

        sessions = [
            s for s in self.time_tracker.sessions.values()
            if s.student_id == student_id and s.total_time > 0
        ]

        if not sessions:
            return 0

        avg = sum(s.focused_time for s in sessions) / len(sessions)
        return int(avg)

    def _calculate_subject_progress(self, student_id: str) -> Dict[str, float]:
        """Calculate mastery by subject"""
        if not self.knowledge_graph:
            return {}

        knowledge_map = self.knowledge_graph.get_student_knowledge_map(student_id)
        subject_masteries = {}

        for concept_id, state in knowledge_map.items():
            concept = self.knowledge_graph.get_concept(concept_id)
            if concept:
                subject = concept.subject
                if subject not in subject_masteries:
                    subject_masteries[subject] = []
                subject_masteries[subject].append(state["mastery_level"])

        # Average mastery per subject
        return {
            subject: sum(levels) / len(levels)
            for subject, levels in subject_masteries.items()
        }

    def _identify_strengths(self, student_id: str) -> List[str]:
        """Identify student's strengths"""
        subjects = self._calculate_subject_progress(student_id)
        strengths = [
            subject for subject, mastery in subjects.items()
            if mastery >= 0.7
        ]
        return strengths

    def _identify_improvement_areas(self, student_id: str) -> List[str]:
        """Identify areas needing improvement"""
        if not self.knowledge_graph:
            return []

        weak_areas = self.knowledge_graph.get_weak_areas(student_id, threshold=0.6)
        return [
            self.knowledge_graph.get_concept(area_id).chapter
            for area_id in weak_areas[:3]
            if self.knowledge_graph.get_concept(area_id)
        ]

    def _calculate_productivity_score(self, student_id: str) -> float:
        """Calculate overall productivity score"""
        if not self.time_tracker:
            return 0.5

        # Average productivity over last 7 days
        trend = self._calculate_productivity_trend(student_id, days=7)
        return sum(trend) / len(trend) if trend else 0.5

    def _calculate_consistency_score(self, student_id: str) -> float:
        """Calculate study consistency score"""
        # Based on streak and regularity
        streak = self._calculate_streak(student_id)
        consistency = min(streak / 7.0, 1.0)  # Max at 7-day streak
        return consistency

    def _classify_engagement(self, productivity: float, consistency: float) -> str:
        """Classify engagement level"""
        avg = (productivity + consistency) / 2

        if avg >= 0.7:
            return "high"
        elif avg >= 0.4:
            return "medium"
        else:
            return "low"

    def _generate_weekly_summary(self, student_id: str) -> str:
        """Generate AI-powered weekly summary for parents"""
        week_time = self._calculate_study_time(student_id, days=7)
        subjects = self._calculate_subject_progress(student_id)

        summary = f"This week, your child studied for {week_time // 60} minutes. "

        if subjects:
            best_subject = max(subjects, key=subjects.get)
            summary += f"They're showing strong progress in {best_subject}. "

        productivity = self._calculate_productivity_score(student_id)
        if productivity >= 0.7:
            summary += "Focus and engagement levels are excellent."
        elif productivity >= 0.4:
            summary += "Engagement is steady, with room for improvement."
        else:
            summary += "Consider discussing study habits and motivation."

        return summary

    def _generate_parent_recommendations(self, student_id: str) -> List[str]:
        """Generate recommendations for parents"""
        recommendations = []

        # Check consistency
        consistency = self._calculate_consistency_score(student_id)
        if consistency < 0.5:
            recommendations.append("Help establish a regular study routine")

        # Check improvement areas
        improvement_areas = self._identify_improvement_areas(student_id)
        if improvement_areas:
            recommendations.append(f"Consider extra support in {improvement_areas[0]}")

        # Check engagement
        productivity = self._calculate_productivity_score(student_id)
        if productivity < 0.4:
            recommendations.append("Discuss challenges and motivation with your child")

        if not recommendations:
            recommendations.append("Keep up the great work and support!")

        return recommendations

    def _calculate_weekly_trend(self, student_id: str, weeks: int) -> List[int]:
        """Calculate study time for each of past N weeks"""
        trend = []

        for i in range(weeks):
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)

            week_time = sum(
                session.focused_time
                for session in self.time_tracker.sessions.values()
                if (session.student_id == student_id and
                    week_start <= session.start_time < week_end)
            ) if self.time_tracker else 0

            trend.append(week_time)

        return list(reversed(trend))

    def _calculate_progress_trend(self, student_id: str, weeks: int) -> List[float]:
        """Calculate overall mastery trend over weeks"""
        # Simplified - in production, maintain historical snapshots
        current_progress = self._calculate_path_progress(student_id)

        # Simulate trend (in production, use actual historical data)
        return [current_progress * (0.6 + i * 0.1) for i in range(weeks)]

    def export_dashboard(self, dashboard: DashboardData, filepath: str):
        """Export dashboard to JSON"""
        data = asdict(dashboard)

        # Convert datetime objects to ISO format
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=convert_datetime)


# Example usage
if __name__ == "__main__":
    print("Dashboard Generator - Test Mode")
    print("=" * 50)

    generator = DashboardGenerator()

    student_id = "student_001"

    # Generate student dashboard
    print("\n📊 Generating Student Dashboard...")
    student_dash = generator.generate_student_dashboard(student_id)

    print(f"\n✓ Student Dashboard Generated:")
    print(f"  - Study time today: {student_dash.today_study_time // 60} minutes")
    print(f"  - Current streak: {student_dash.current_streak} days")
    print(f"  - Topics mastered: {len(student_dash.topics_mastered)}")
    print(f"  - AI interactions: {student_dash.ai_interactions_count}")

    # Generate parent dashboard
    print("\n📊 Generating Parent Dashboard...")
    parent_dash = generator.generate_parent_dashboard(student_id)

    print(f"\n✓ Parent Dashboard Generated (Privacy-Safe):")
    print(f"  - Week total time: {parent_dash.week_total_time // 60} minutes")
    print(f"  - Productivity score: {parent_dash.productivity_score:.1%}")
    print(f"  - Engagement level: {parent_dash.engagement_level}")
    print(f"  - Weekly summary: {parent_dash.weekly_summary}")

    print("\n✓ Privacy Note: Parent dashboard shows only aggregated data")
    print("✓ No live surveillance or real-time monitoring")
