"""
AI Companion Chat System
Provides empathetic, context-aware companionship with multiple interaction modes.
Modes: Guide (educational), Coach (motivational), Friend (emotional support).
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import random


class CompanionMode(Enum):
    """AI companion interaction modes"""
    GUIDE = "guide"  # Educational support, explains concepts
    COACH = "coach"  # Motivational, tracks progress, encourages
    FRIEND = "friend"  # Emotional support, casual conversation


@dataclass
class ConversationContext:
    """Context for conversation generation"""
    student_id: str
    current_state: str  # Learning state
    time_in_state: int  # seconds
    recent_topics: List[str]
    mastery_levels: Dict[str, float]
    session_duration: int  # seconds
    productivity_ratio: float
    recent_achievements: List[str]
    detected_emotion: str
    last_intervention_time: Optional[datetime]


@dataclass
class CompanionMessage:
    """AI companion message"""
    timestamp: datetime
    mode: CompanionMode
    message: str
    intent: str  # "encourage", "explain", "motivate", "empathize", "suggest"
    requires_response: bool
    suggested_responses: List[str]


@dataclass
class InterventionRule:
    """Rule for when AI should intervene"""
    rule_id: str
    trigger_condition: str
    cooldown_minutes: int  # Minimum time between interventions
    mode: CompanionMode
    priority: int  # Higher = more urgent


class AICompanion:
    """
    Intelligent AI companion that adapts to student's learning and emotional state.
    Provides context-aware interventions and support.
    """

    def __init__(self,
                 personality: str = "encouraging",
                 default_mode: CompanionMode = CompanionMode.COACH):
        """
        Initialize AI companion.

        Args:
            personality: "encouraging", "strict", "playful", "academic"
            default_mode: Default interaction mode
        """
        self.personality = personality
        self.default_mode = default_mode
        self.conversation_history: List[CompanionMessage] = []
        self.intervention_history: Dict[str, datetime] = {}

        # Define intervention rules
        self.intervention_rules = self._initialize_intervention_rules()

        # Message templates by mode and intent
        self.message_templates = self._load_message_templates()

    def _initialize_intervention_rules(self) -> List[InterventionRule]:
        """Define when AI should intervene"""
        return [
            InterventionRule(
                rule_id="idle_too_long",
                trigger_condition="idle_time > 180",
                cooldown_minutes=5,
                mode=CompanionMode.FRIEND,
                priority=7
            ),
            InterventionRule(
                rule_id="long_focus_session",
                trigger_condition="focused_time > 1500",  # 25 minutes
                cooldown_minutes=30,
                mode=CompanionMode.COACH,
                priority=5
            ),
            InterventionRule(
                rule_id="confusion_detected",
                trigger_condition="emotion == confused AND time_in_state > 300",
                cooldown_minutes=10,
                mode=CompanionMode.GUIDE,
                priority=8
            ),
            InterventionRule(
                rule_id="fatigue_detected",
                trigger_condition="emotion == tired",
                cooldown_minutes=15,
                mode=CompanionMode.FRIEND,
                priority=9
            ),
            InterventionRule(
                rule_id="achievement_unlocked",
                trigger_condition="new_achievement",
                cooldown_minutes=0,
                mode=CompanionMode.COACH,
                priority=6
            ),
            InterventionRule(
                rule_id="distraction_pattern",
                trigger_condition="distraction_count > 3",
                cooldown_minutes=20,
                mode=CompanionMode.COACH,
                priority=7
            ),
        ]

    def _load_message_templates(self) -> Dict:
        """
        Load message templates for different modes and intents.
        In production, load from database or configuration.
        """
        return {
            CompanionMode.GUIDE: {
                "explain": [
                    "Let me help you understand this concept. {explanation}",
                    "Here's a way to think about it: {explanation}",
                    "This topic builds on what you learned earlier. {explanation}",
                ],
                "hint": [
                    "Have you tried {hint}?",
                    "Think about how this relates to {related_concept}.",
                    "What if you approached it from {alternative_angle}?",
                ],
                "check_understanding": [
                    "Does this make sense so far?",
                    "Want me to explain any part in more detail?",
                    "Ready to try a practice problem?",
                ]
            },
            CompanionMode.COACH: {
                "motivate": [
                    "You're doing great! Keep up the momentum!",
                    "I can see you're making real progress on {topic}.",
                    "You've stayed focused for {duration} minutes—that's impressive!",
                ],
                "celebrate": [
                    "Awesome! You just completed {achievement}!",
                    "Wow! {achievement}—you're on fire today!",
                    "Great work! You're {percent}% better than yesterday!",
                ],
                "goal_setting": [
                    "You've completed {count} problems. Can you do {target} today?",
                    "Want to aim for {goal_minutes} minutes of focused study?",
                    "Let's set a goal: master {concept} by end of session!",
                ],
                "progress_update": [
                    "You've studied for {time} today. Your mastery in {topic} is now {percent}%!",
                    "Quick update: {focused_time} minutes of quality focus time today!",
                ]
            },
            CompanionMode.FRIEND: {
                "empathize": [
                    "I notice you've been working hard. How are you feeling?",
                    "This problem looks challenging. Don't be too hard on yourself!",
                    "It's okay to take breaks. Your brain needs them!",
                ],
                "suggest_break": [
                    "You've been at this for {duration} minutes. Want a 5-minute break?",
                    "How about stretching for a minute? It helps with focus!",
                    "Quick break? Sometimes stepping away helps you see things clearer.",
                ],
                "check_in": [
                    "Everything going okay?",
                    "Need anything? I'm here to help!",
                    "How's the energy level? Still good?",
                ],
                "encourage": [
                    "You've got this! I believe in you.",
                    "Challenges make us stronger. Keep going!",
                    "Every expert was once a beginner. You're doing fine!",
                ]
            }
        }

    def evaluate_intervention(self, context: ConversationContext) -> Optional[CompanionMessage]:
        """
        Evaluate if AI should intervene based on current context.

        Args:
            context: Current learning and emotional context

        Returns:
            CompanionMessage if intervention needed, None otherwise
        """
        # Check each intervention rule
        triggered_rules = []

        for rule in self.intervention_rules:
            # Check cooldown
            if rule.rule_id in self.intervention_history:
                last_intervention = self.intervention_history[rule.rule_id]
                time_since = (datetime.now() - last_intervention).total_seconds() / 60

                if time_since < rule.cooldown_minutes:
                    continue  # Still in cooldown

            # Evaluate trigger condition
            if self._evaluate_condition(rule.trigger_condition, context):
                triggered_rules.append(rule)

        if not triggered_rules:
            return None

        # Select highest priority rule
        triggered_rules.sort(key=lambda r: r.priority, reverse=True)
        selected_rule = triggered_rules[0]

        # Generate message based on rule
        message = self._generate_intervention_message(selected_rule, context)

        # Record intervention
        self.intervention_history[selected_rule.rule_id] = datetime.now()
        self.conversation_history.append(message)

        return message

    def _evaluate_condition(self, condition: str, context: ConversationContext) -> bool:
        """
        Evaluate trigger condition.
        Simple evaluation - in production, use a proper expression evaluator.
        """
        # Parse simple conditions
        if "idle_time >" in condition:
            threshold = int(condition.split(">")[1].strip())
            if context.current_state == "idle":
                return context.time_in_state > threshold

        if "focused_time >" in condition:
            threshold = int(condition.split(">")[1].strip())
            if context.current_state == "active":
                return context.time_in_state > threshold

        if "emotion == confused" in condition:
            return context.detected_emotion == "confused"

        if "emotion == tired" in condition:
            return context.detected_emotion == "tired" or context.detected_emotion == "fatigued"

        if "new_achievement" in condition:
            return len(context.recent_achievements) > 0

        if "distraction_count >" in condition:
            # This would come from session data
            return False

        return False

    def _generate_intervention_message(self,
                                      rule: InterventionRule,
                                      context: ConversationContext) -> CompanionMessage:
        """Generate appropriate message for the triggered rule"""
        mode = rule.mode

        # Select intent based on rule
        intent_map = {
            "idle_too_long": "suggest_break",
            "long_focus_session": "motivate",
            "confusion_detected": "hint",
            "fatigue_detected": "suggest_break",
            "achievement_unlocked": "celebrate",
            "distraction_pattern": "motivate"
        }

        intent = intent_map.get(rule.rule_id, "encourage")

        # Get template and fill with context
        message_text = self._fill_template(mode, intent, context)

        # Determine if response is needed
        requires_response = intent in ["check_in", "check_understanding", "suggest_break"]

        # Generate suggested responses
        suggested_responses = self._generate_suggested_responses(intent)

        return CompanionMessage(
            timestamp=datetime.now(),
            mode=mode,
            message=message_text,
            intent=intent,
            requires_response=requires_response,
            suggested_responses=suggested_responses
        )

    def _fill_template(self,
                      mode: CompanionMode,
                      intent: str,
                      context: ConversationContext) -> str:
        """Fill message template with context data"""
        templates = self.message_templates.get(mode, {}).get(intent, [])

        if not templates:
            return "Keep up the good work!"

        template = random.choice(templates)

        # Fill placeholders
        replacements = {
            "topic": context.recent_topics[0] if context.recent_topics else "this topic",
            "duration": str(context.time_in_state // 60),
            "achievement": context.recent_achievements[0] if context.recent_achievements else "something great",
            "percent": "85",  # Calculate from context
            "count": "5",
            "target": "7",
            "goal_minutes": "30",
            "concept": context.recent_topics[0] if context.recent_topics else "this concept",
            "time": f"{context.session_duration // 60} minutes",
            "focused_time": f"{int(context.session_duration * context.productivity_ratio) // 60}",
        }

        for key, value in replacements.items():
            template = template.replace(f"{{{key}}}", str(value))

        return template

    def _generate_suggested_responses(self, intent: str) -> List[str]:
        """Generate quick response options for student"""
        response_map = {
            "suggest_break": ["Yes, take a break", "No, keep studying", "Just 5 more minutes"],
            "check_in": ["I'm good!", "Need help", "Feeling stuck"],
            "check_understanding": ["Yes, got it!", "Explain more please", "Show an example"],
            "hint": ["Thanks!", "Try another hint", "I'll figure it out"],
        }

        return response_map.get(intent, ["Thanks!", "Okay!"])

    def generate_response(self,
                         student_message: str,
                         context: ConversationContext,
                         mode: Optional[CompanionMode] = None) -> CompanionMessage:
        """
        Generate response to student's message.

        Args:
            student_message: What the student said
            context: Current context
            mode: Specific mode to use (or default)

        Returns:
            CompanionMessage response
        """
        use_mode = mode or self.default_mode

        # Analyze student message sentiment/intent
        intent = self._analyze_message_intent(student_message)

        # Generate appropriate response
        if intent == "help_request":
            response = self._generate_help_response(student_message, context)
        elif intent == "frustration":
            response = self._generate_empathy_response(student_message, context)
        elif intent == "achievement":
            response = self._generate_celebration_response(student_message, context)
        else:
            response = self._generate_general_response(student_message, context)

        message = CompanionMessage(
            timestamp=datetime.now(),
            mode=use_mode,
            message=response,
            intent=intent,
            requires_response=False,
            suggested_responses=[]
        )

        self.conversation_history.append(message)
        return message

    def _analyze_message_intent(self, message: str) -> str:
        """Analyze what student is trying to communicate"""
        message_lower = message.lower()

        # Simple keyword-based intent detection
        # In production, use NLP intent classification
        if any(word in message_lower for word in ["help", "don't understand", "confused", "stuck"]):
            return "help_request"

        if any(word in message_lower for word in ["frustrated", "difficult", "hard", "can't"]):
            return "frustration"

        if any(word in message_lower for word in ["finished", "completed", "done", "solved"]):
            return "achievement"

        return "general"

    def _generate_help_response(self, message: str, context: ConversationContext) -> str:
        """Generate helpful response when student asks for help"""
        topic = context.recent_topics[0] if context.recent_topics else "this"

        responses = [
            f"I'm here to help! What specifically about {topic} is confusing?",
            f"No problem! Let's break {topic} down step by step.",
            f"That's what I'm here for! Can you show me where you got stuck with {topic}?",
        ]

        return random.choice(responses)

    def _generate_empathy_response(self, message: str, context: ConversationContext) -> str:
        """Generate empathetic response to frustration"""
        responses = [
            "I understand this is challenging. Take a deep breath—you're capable of this!",
            "It's okay to feel frustrated. This topic takes time to master. Want to try a different approach?",
            "I can see you're working hard. Sometimes taking a short break helps things click!",
            "You're not alone in finding this difficult. Let's tackle it together, one step at a time.",
        ]

        return random.choice(responses)

    def _generate_celebration_response(self, message: str, context: ConversationContext) -> str:
        """Celebrate student's achievement"""
        responses = [
            "Excellent work! You should be proud of that progress!",
            "Wow, that's fantastic! See what you can do when you focus?",
            "Great job! You're building real understanding now!",
            "That's awesome! Your hard work is paying off!",
        ]

        return random.choice(responses)

    def _generate_general_response(self, message: str, context: ConversationContext) -> str:
        """Generate general conversational response"""
        responses = [
            "I'm listening! What's on your mind?",
            "Tell me more!",
            "Interesting! How does that relate to what you're studying?",
            "I'm here if you need anything!",
        ]

        return random.choice(responses)

    def get_conversation_history(self, limit: int = 10) -> List[CompanionMessage]:
        """Get recent conversation history"""
        return self.conversation_history[-limit:]


# Example usage
if __name__ == "__main__":
    print("AI Companion Chat System - Test Mode")
    print("=" * 50)

    companion = AICompanion(personality="encouraging")

    # Create context
    context = ConversationContext(
        student_id="student_001",
        current_state="active",
        time_in_state=1600,  # 26+ minutes
        recent_topics=["Quadratic Equations"],
        mastery_levels={"math_algebra_quadratic": 0.65},
        session_duration=1800,
        productivity_ratio=0.85,
        recent_achievements=[],
        detected_emotion="focused",
        last_intervention_time=None
    )

    print("\n🤖 Testing intervention evaluation...")

    # Should trigger long focus session intervention
    message = companion.evaluate_intervention(context)

    if message:
        print(f"\n💬 AI Companion ({message.mode.value} mode):")
        print(f"   {message.message}")
        print(f"   Intent: {message.intent}")

        if message.suggested_responses:
            print(f"   Quick replies: {', '.join(message.suggested_responses)}")

    # Test student interaction
    print("\n👤 Student: 'I don't understand this problem'")

    response = companion.generate_response(
        "I don't understand this problem",
        context,
        mode=CompanionMode.GUIDE
    )

    print(f"\n🤖 AI Companion ({response.mode.value} mode):")
    print(f"   {response.message}")

    print("\n✓ AI Companion system operational")
    print(f"✓ Supports {len(CompanionMode)} interaction modes")
    print(f"✓ {len(companion.intervention_rules)} intervention rules active")
