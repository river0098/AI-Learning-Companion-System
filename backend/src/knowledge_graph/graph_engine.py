"""
Knowledge Graph Engine
Maps learning content to knowledge domains and builds personalized learning paths.
Tracks mastery levels and suggests next learning steps.
"""

import json
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict
import networkx as nx


@dataclass
class Concept:
    """Represents a single learning concept"""
    id: str
    name: str
    subject: str
    chapter: str
    difficulty: str  # "easy", "medium", "hard"
    prerequisites: List[str]  # IDs of prerequisite concepts
    description: str


@dataclass
class MasteryState:
    """Tracks student's mastery of a concept"""
    concept_id: str
    mastery_level: float  # 0.0 to 1.0
    last_practiced: datetime
    exercises_completed: int
    exercises_correct: int
    total_time_spent: int  # seconds
    first_learned: datetime


@dataclass
class LearningPath:
    """Recommended sequence of concepts to learn"""
    path_id: str
    goal_concept: str
    ordered_concepts: List[str]
    estimated_time: int  # minutes
    difficulty_profile: str  # "gradual", "steep", "mixed"


class KnowledgeGraphEngine:
    """
    Manages knowledge graph and learning path generation.
    Uses NetworkX for graph operations.
    """

    def __init__(self):
        """Initialize knowledge graph"""
        self.graph = nx.DiGraph()  # Directed graph for prerequisites
        self.concepts: Dict[str, Concept] = {}
        self.mastery_states: Dict[str, Dict[str, MasteryState]] = defaultdict(dict)

        # Initialize with base knowledge structure
        self._initialize_base_graph()

    def _initialize_base_graph(self):
        """
        Initialize with common academic knowledge structure.
        In production, load from a comprehensive knowledge database.
        """
        # Math concepts example
        math_concepts = [
            Concept(
                id="math_arithmetic_addition",
                name="Addition",
                subject="Math",
                chapter="Arithmetic",
                difficulty="easy",
                prerequisites=[],
                description="Basic addition of numbers"
            ),
            Concept(
                id="math_arithmetic_subtraction",
                name="Subtraction",
                subject="Math",
                chapter="Arithmetic",
                difficulty="easy",
                prerequisites=["math_arithmetic_addition"],
                description="Basic subtraction of numbers"
            ),
            Concept(
                id="math_algebra_linear_equations",
                name="Linear Equations",
                subject="Math",
                chapter="Algebra",
                difficulty="medium",
                prerequisites=["math_arithmetic_addition", "math_arithmetic_subtraction"],
                description="Solving equations like 2x + 3 = 7"
            ),
            Concept(
                id="math_algebra_quadratic_equations",
                name="Quadratic Equations",
                subject="Math",
                chapter="Algebra",
                difficulty="hard",
                prerequisites=["math_algebra_linear_equations"],
                description="Solving equations like x² + 2x + 1 = 0"
            ),
            Concept(
                id="math_algebra_systems",
                name="Systems of Equations",
                subject="Math",
                chapter="Algebra",
                difficulty="hard",
                prerequisites=["math_algebra_linear_equations"],
                description="Solving multiple equations simultaneously"
            ),
        ]

        # Physics concepts example
        physics_concepts = [
            Concept(
                id="physics_mechanics_motion",
                name="Kinematics",
                subject="Physics",
                chapter="Mechanics",
                difficulty="medium",
                prerequisites=["math_algebra_linear_equations"],
                description="Study of motion: velocity, acceleration"
            ),
            Concept(
                id="physics_mechanics_forces",
                name="Forces and Newton's Laws",
                subject="Physics",
                chapter="Mechanics",
                difficulty="medium",
                prerequisites=["physics_mechanics_motion"],
                description="Forces, mass, and acceleration"
            ),
        ]

        # Add all concepts to graph
        all_concepts = math_concepts + physics_concepts

        for concept in all_concepts:
            self.add_concept(concept)

    def add_concept(self, concept: Concept):
        """
        Add a new concept to the knowledge graph.

        Args:
            concept: Concept to add
        """
        self.concepts[concept.id] = concept
        self.graph.add_node(concept.id, **asdict(concept))

        # Add prerequisite edges
        for prereq_id in concept.prerequisites:
            if prereq_id in self.concepts:
                self.graph.add_edge(prereq_id, concept.id, relation="prerequisite")

    def get_concept(self, concept_id: str) -> Optional[Concept]:
        """Get concept by ID"""
        return self.concepts.get(concept_id)

    def find_concepts_by_topic(self, topic_keywords: List[str]) -> List[Concept]:
        """
        Find concepts matching topic keywords.

        Args:
            topic_keywords: List of keywords to search

        Returns:
            List of matching concepts
        """
        matches = []

        for concept in self.concepts.values():
            # Check if any keyword matches concept name or description
            for keyword in topic_keywords:
                keyword_lower = keyword.lower()
                if (keyword_lower in concept.name.lower() or
                    keyword_lower in concept.description.lower() or
                    keyword_lower in concept.subject.lower() or
                    keyword_lower in concept.chapter.lower()):
                    matches.append(concept)
                    break

        return matches

    def update_mastery(self,
                      student_id: str,
                      concept_id: str,
                      exercise_result: Dict):
        """
        Update student's mastery level for a concept.

        Args:
            student_id: Student identifier
            concept_id: Concept being practiced
            exercise_result: Dict with keys:
                - correct: bool
                - time_spent: int (seconds)
                - difficulty: str
        """
        if concept_id not in self.concepts:
            return

        # Get or create mastery state
        if concept_id not in self.mastery_states[student_id]:
            self.mastery_states[student_id][concept_id] = MasteryState(
                concept_id=concept_id,
                mastery_level=0.0,
                last_practiced=datetime.now(),
                exercises_completed=0,
                exercises_correct=0,
                total_time_spent=0,
                first_learned=datetime.now()
            )

        state = self.mastery_states[student_id][concept_id]

        # Update statistics
        state.exercises_completed += 1
        if exercise_result.get("correct", False):
            state.exercises_correct += 1

        state.total_time_spent += exercise_result.get("time_spent", 0)
        state.last_practiced = datetime.now()

        # Calculate new mastery level
        accuracy = state.exercises_correct / state.exercises_completed
        experience_factor = min(state.exercises_completed / 20, 1.0)  # Caps at 20 exercises

        # Mastery formula: weighted average of accuracy and experience
        state.mastery_level = 0.7 * accuracy + 0.3 * experience_factor

    def get_mastery_level(self,
                         student_id: str,
                         concept_id: str) -> float:
        """
        Get student's mastery level for a concept.

        Returns:
            Mastery level from 0.0 to 1.0
        """
        if concept_id in self.mastery_states.get(student_id, {}):
            return self.mastery_states[student_id][concept_id].mastery_level
        return 0.0

    def get_student_knowledge_map(self, student_id: str) -> Dict:
        """
        Get complete knowledge map for a student.

        Returns:
            Dictionary mapping concept IDs to mastery states
        """
        return {
            concept_id: asdict(state)
            for concept_id, state in self.mastery_states.get(student_id, {}).items()
        }

    def generate_learning_path(self,
                               student_id: str,
                               goal_concept_id: str) -> Optional[LearningPath]:
        """
        Generate personalized learning path to reach a goal concept.

        Args:
            student_id: Student identifier
            goal_concept_id: Target concept to learn

        Returns:
            LearningPath with ordered sequence of concepts
        """
        if goal_concept_id not in self.concepts:
            return None

        # Get all prerequisites using graph traversal
        prerequisites = self._get_all_prerequisites(goal_concept_id)

        # Filter to only concepts not yet mastered
        concepts_to_learn = [
            concept_id for concept_id in prerequisites
            if self.get_mastery_level(student_id, concept_id) < 0.8
        ]

        # Add goal concept if not mastered
        if self.get_mastery_level(student_id, goal_concept_id) < 0.8:
            concepts_to_learn.append(goal_concept_id)

        # Order concepts by prerequisites (topological sort)
        ordered_concepts = self._topological_sort(concepts_to_learn)

        # Estimate time based on concept difficulties
        estimated_time = self._estimate_learning_time(ordered_concepts)

        # Determine difficulty profile
        difficulty_profile = self._analyze_difficulty_profile(ordered_concepts)

        return LearningPath(
            path_id=f"path_{student_id}_{goal_concept_id}_{datetime.now().timestamp()}",
            goal_concept=goal_concept_id,
            ordered_concepts=ordered_concepts,
            estimated_time=estimated_time,
            difficulty_profile=difficulty_profile
        )

    def suggest_next_concept(self, student_id: str) -> Optional[str]:
        """
        Suggest the next concept to learn based on current mastery.

        Returns:
            Concept ID to study next
        """
        # Find concepts where prerequisites are mastered but concept itself isn't
        candidates = []

        for concept_id, concept in self.concepts.items():
            # Skip if already mastered
            if self.get_mastery_level(student_id, concept_id) >= 0.8:
                continue

            # Check if all prerequisites are mastered
            prereqs_mastered = all(
                self.get_mastery_level(student_id, prereq_id) >= 0.7
                for prereq_id in concept.prerequisites
            )

            if prereqs_mastered:
                candidates.append(concept_id)

        if not candidates:
            return None

        # Sort by difficulty and return easiest
        candidates.sort(key=lambda cid: self.concepts[cid].difficulty)
        return candidates[0]

    def get_weak_areas(self, student_id: str, threshold: float = 0.5) -> List[str]:
        """
        Identify concepts where student is struggling.

        Args:
            student_id: Student identifier
            threshold: Mastery level below which concept is considered weak

        Returns:
            List of concept IDs with low mastery
        """
        weak_areas = []

        for concept_id, state in self.mastery_states.get(student_id, {}).items():
            if state.mastery_level < threshold and state.exercises_completed > 3:
                weak_areas.append(concept_id)

        return weak_areas

    def _get_all_prerequisites(self, concept_id: str) -> List[str]:
        """
        Get all prerequisites for a concept (recursive).
        """
        if concept_id not in self.graph:
            return []

        # Use NetworkX to find all ancestors (prerequisites)
        prerequisites = list(nx.ancestors(self.graph, concept_id))
        return prerequisites

    def _topological_sort(self, concept_ids: List[str]) -> List[str]:
        """
        Order concepts by prerequisites using topological sort.
        """
        # Create subgraph with only relevant concepts
        subgraph = self.graph.subgraph(concept_ids)

        try:
            # Topological sort ensures prerequisites come first
            ordered = list(nx.topological_sort(subgraph))
            return ordered
        except nx.NetworkXError:
            # If graph has cycles, return original order
            return concept_ids

    def _estimate_learning_time(self, concept_ids: List[str]) -> int:
        """
        Estimate time needed to learn concepts (in minutes).
        """
        time_by_difficulty = {
            "easy": 30,
            "medium": 60,
            "hard": 90
        }

        total_time = sum(
            time_by_difficulty.get(self.concepts[cid].difficulty, 60)
            for cid in concept_ids
            if cid in self.concepts
        )

        return total_time

    def _analyze_difficulty_profile(self, concept_ids: List[str]) -> str:
        """
        Analyze difficulty progression in learning path.
        """
        if not concept_ids:
            return "empty"

        difficulties = [
            self.concepts[cid].difficulty
            for cid in concept_ids
            if cid in self.concepts
        ]

        if not difficulties:
            return "unknown"

        # Check if difficulty increases gradually
        difficulty_values = {"easy": 1, "medium": 2, "hard": 3}
        values = [difficulty_values[d] for d in difficulties]

        # Calculate progression
        if all(values[i] <= values[i+1] for i in range(len(values)-1)):
            return "gradual"
        elif values[-1] - values[0] >= 2:
            return "steep"
        else:
            return "mixed"

    def export_graph(self, filepath: str):
        """Export knowledge graph to JSON"""
        data = {
            "concepts": {cid: asdict(c) for cid, c in self.concepts.items()},
            "edges": list(self.graph.edges()),
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    print("Knowledge Graph Engine - Test Mode")
    print("=" * 50)

    engine = KnowledgeGraphEngine()

    print(f"\n📚 Initialized with {len(engine.concepts)} concepts")

    # Simulate student learning
    student_id = "student_001"

    print("\n✏️ Simulating student practice sessions...")

    # Practice basic concepts
    engine.update_mastery(student_id, "math_arithmetic_addition", {
        "correct": True,
        "time_spent": 120
    })

    engine.update_mastery(student_id, "math_arithmetic_subtraction", {
        "correct": True,
        "time_spent": 150
    })

    # Get knowledge map
    knowledge_map = engine.get_student_knowledge_map(student_id)
    print(f"\n📊 Current Knowledge Map:")
    for concept_id, state in knowledge_map.items():
        print(f"  - {concept_id}: {state['mastery_level']:.1%} mastery")

    # Suggest next concept
    next_concept = engine.suggest_next_concept(student_id)
    if next_concept:
        concept = engine.get_concept(next_concept)
        print(f"\n💡 Suggested next concept: {concept.name}")
        print(f"   Subject: {concept.subject} - {concept.chapter}")
        print(f"   Difficulty: {concept.difficulty}")

    # Generate learning path
    path = engine.generate_learning_path(student_id, "math_algebra_quadratic_equations")
    if path:
        print(f"\n🎯 Learning Path to Quadratic Equations:")
        print(f"   Estimated time: {path.estimated_time} minutes")
        print(f"   Difficulty profile: {path.difficulty_profile}")
        print(f"   Steps:")
        for i, concept_id in enumerate(path.ordered_concepts, 1):
            concept = engine.get_concept(concept_id)
            print(f"     {i}. {concept.name} ({concept.difficulty})")
