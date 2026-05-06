"""
Phase 19 — Quantum Education Module.

Interactive tutorials, quantum concepts visualization, progress tracking.
"""
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import time


class TutorialLevel(Enum):
    """Tutorial difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ConceptType(Enum):
    """Types of quantum concepts."""
    SUPERPOSITION = "superposition"
    ENTANGLEMENT = "entanglement"
    MEASUREMENT = "measurement"
    GATES = "gates"
    CIRCUITS = "circuits"
    ALGORITHMS = "algorithms"


@dataclass
class QuantumConcept:
    """Representation of a quantum concept."""
    name: str
    type: ConceptType
    description: str
    level: TutorialLevel
    prerequisites: List[str] = field(default_factory=list)
    qubits_needed: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'level': self.level.value,
            'prerequisites': self.prerequisites,
            'qubits_needed': self.qubits_needed,
        }


@dataclass
class TutorialStep:
    """A step in a tutorial."""
    step_id: str
    title: str
    content: str
    code_example: Optional[str] = None
    expected_output: Optional[str] = None
    qubits_used: int = 1
    interactive: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'title': self.title,
            'content': self.content,
            'code_example': self.code_example,
            'expected_output': self.expected_output,
            'qubits_used': self.qubits_used,
            'interactive': self.interactive,
        }


@dataclass
class Tutorial:
    """A complete tutorial."""
    tutorial_id: str
    title: str
    level: TutorialLevel
    concept: ConceptType
    steps: List[TutorialStep] = field(default_factory=list)
    author: str = "AbirQu Team"
    created_at: float = field(default_factory=time.time)
    completion_time_min: int = 30

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tutorial_id': self.tutorial_id,
            'title': self.title,
            'level': self.level.value,
            'concept': self.concept.value,
            'num_steps': len(self.steps),
            'author': self.author,
            'completion_time_min': self.completion_time_min,
        }

    def build_quantum_state(self, step_index: int) -> np.ndarray:
        """Build quantum state for a step's code example."""
        if step_index >= len(self.steps):
            return np.array([1.0] + [0.0] * 15, dtype=complex)  # |00...0>

        step = self.steps[step_index]
        if not step.code_example:
            return np.array([1.0] + [0.0] * 15, dtype=complex)

        # Parse and execute simple quantum code
        n = 2 ** step.qubits_used
        state = np.zeros(n, dtype=complex)
        state[0] = 1.0  # Start with |00...0>

        # Very simple parser for demonstration
        lines = step.code_example.strip().split('\n')
        for line in lines:
            line = line.strip().lower()
            if 'h(' in line:
                # Extract qubit
                try:
                    qubit = int(line.split('h(')[1].split(')')[0])
                    # Apply H gate
                    new_state = np.zeros_like(state)
                    for i in range(n):
                        bit = (i >> qubit) & 1
                        j = i ^ (1 << qubit)
                        inv_sqrt2 = 1.0 / np.sqrt(2.0)
                        if bit == 0:
                            new_state[i] += inv_sqrt2 * state[i]
                            new_state[j] += inv_sqrt2 * state[j]
                        else:
                            new_state[i] += inv_sqrt2 * state[i]
                            new_state[j] += -inv_sqrt2 * state[j]
                    state = new_state / np.linalg.norm(new_state)
                except:
                    pass
            elif 'x(' in line:
                try:
                    qubit = int(line.split('x(')[1].split(')')[0])
                    new_state = np.zeros_like(state)
                    for i in range(n):
                        bit = (i >> qubit) & 1
                        j = i ^ (1 << qubit)
                        if bit == 0:
                            new_state[i] = state[j]
                        else:
                            new_state[j] = state[i]
                    state = new_state / np.linalg.norm(new_state)
                except:
                    pass
            elif 'cnot(' in line or 'cx(' in line:
                try:
                    part = line.split('(')[1].split(')')[0]
                    q1, q2 = map(int, part.split(','))
                    new_state = np.zeros_like(state)
                    for i in range(n):
                        bit1 = (i >> q1) & 1
                        if bit1 == 1:
                            j = i ^ (1 << q2)
                            new_state[j] = state[i]
                        else:
                            new_state[i] = state[i]
                    state = new_state / np.linalg.norm(new_state)
                except:
                    pass

        return state

    def measure_state(self, state: np.ndarray) -> Dict[str, int]:
        """Measure quantum state and return counts."""
        probs = np.abs(state) ** 2
        probs = probs / np.sum(probs)

        # Sample measurements
        num_shots = 1000
        counts = {}
        for _ in range(num_shots):
            outcome = np.random.choice(len(state), p=probs)
            key = format(outcome, f'0{step.qubits_used}b')
            counts[key] = counts.get(key, 0) + 1

        return counts


class ProgressTracker:
    """Track user progress through tutorials."""

    def __init__(self):
        self.user_progress: Dict[str, Dict[str, Any]] = {}
        self.completed_tutorials: Dict[str, List[str]] = {}

    def start_tutorial(self, user: str, tutorial_id: str) -> Dict[str, Any]:
        """Start a tutorial for a user."""
        if user not in self.user_progress:
            self.user_progress[user] = {}

        if tutorial_id not in self.user_progress[user]:
            self.user_progress[user][tutorial_id] = {
                'started_at': time.time(),
                'current_step': 0,
                'completed_steps': [],
                'status': 'in_progress',
            }

        return self.user_progress[user][tutorial_id]

    def complete_step(self, user: str, tutorial_id: str, step_id: str) -> bool:
        """Mark a step as completed."""
        if user not in self.user_progress:
            return False
        if tutorial_id not in self.user_progress[user]:
            return False

        progress = self.user_progress[user][tutorial_id]
        if step_id not in progress['completed_steps']:
            progress['completed_steps'].append(step_id)
            return True
        return False

    def complete_tutorial(self, user: str, tutorial_id: str) -> bool:
        """Mark tutorial as completed."""
        if user not in self.user_progress:
            return False
        if tutorial_id not in self.user_progress[user]:
            return False

        progress = self.user_progress[user][tutorial_id]
        progress['status'] = 'completed'
        progress['completed_at'] = time.time()

        if user not in self.completed_tutorials:
            self.completed_tutorials[user] = []
        if tutorial_id not in self.completed_tutorials[user]:
            self.completed_tutorials[user].append(tutorial_id)

        return True

    def get_progress(self, user: str, tutorial_id: Optional[str] = None) -> Dict[str, Any]:
        """Get progress for a user."""
        if user not in self.user_progress:
            return {}

        if tutorial_id:
            return self.user_progress[user].get(tutorial_id, {})

        return self.user_progress[user]

    def get_statistics(self, user: Optional[str] = None) -> Dict[str, Any]:
        """Get progress statistics."""
        if user:
            completed = len(self.completed_tutorials.get(user, []))
            in_progress = sum(1 for t in self.user_progress.get(user, {}).values()
                            if t['status'] == 'in_progress')
            return {
                'completed': completed,
                'in_progress': in_progress,
                'total_tutorials': completed + in_progress,
            }
        else:
            total_users = len(self.user_progress)
            total_completions = sum(len(v) for v in self.completed_tutorials.values())
            return {
                'total_users': total_users,
                'total_completions': total_completions,
                'avg_completions_per_user': total_completions / max(total_users, 1),
            }


class QuantumEducation:
    """Main education module for AbirQu."""

    def __init__(self):
        self.tutorials: Dict[str, Tutorial] = {}
        self.concepts: Dict[str, QuantumConcept] = {}
        self.progress_tracker = ProgressTracker()
        self._initialize_default_content()

    def _initialize_default_content(self):
        """Initialize with default tutorials."""

        # Basic superposition tutorial
        superposition = QuantumConcept(
            name="Quantum Superposition",
            type=ConceptType.SUPERPOSITION,
            description="Learn how qubits can exist in multiple states simultaneously",
            level=TutorialLevel.BEGINNER,
            qubits_needed=1,
        )
        self.concepts['superposition'] = superposition

        steps = [
            TutorialStep(
                step_id="s1",
                title="What is Superposition?",
                content="A qubit can exist in a superposition of |0⟩ and |1⟩ states.",
                qubits_used=1,
            ),
            TutorialStep(
                step_id="s2",
                title="Creating Superposition with H Gate",
                content="The Hadamard (H) gate puts a qubit into superposition.",
                code_example="h(0)",
                expected_output="State: (|0⟩ + |1⟩)/√2",
                qubits_used=1,
            ),
            TutorialStep(
                step_id="s3",
                title="Measuring Superposition",
                content="When measured, superposition collapses to either |0⟩ or |1⟩ with equal probability.",
                code_example="h(0)\nmeasure(0)",
                qubits_used=1,
            ),
        ]

        tutorial = Tutorial(
            tutorial_id="tut_superposition_1",
            title="Introduction to Quantum Superposition",
            level=TutorialLevel.BEGINNER,
            concept=ConceptType.SUPERPOSITION,
            steps=steps,
            completion_time_min=15,
        )
        self.tutorials[tutorial.tutorial_id] = tutorial

        # Entanglement tutorial
        ent_concept = QuantumConcept(
            name="Quantum Entanglement",
            type=ConceptType.ENTANGLEMENT,
            description="Learn how qubits can become correlated",
            level=TutorialLevel.INTERMEDIATE,
            prerequisites=['superposition'],
            qubits_needed=2,
        )
        self.concepts['entanglement'] = ent_concept

        ent_steps = [
            TutorialStep(
                step_id="e1",
                title="What is Entanglement?",
                content="Entangled qubits share correlations that cannot be explained classically.",
                qubits_used=2,
            ),
            TutorialStep(
                step_id="e2",
                title="Creating Bell States",
                content="Use H and CNOT gates to create an entangled Bell state.",
                code_example="h(0)\ncnot(0,1)",
                expected_output="Bell state: (|00⟩ + |11⟩)/√2",
                qubits_used=2,
            ),
            TutorialStep(
                step_id="e3",
                title="Measuring Entangled States",
                content="Measuring one qubit instantly determines the other.",
                code_example="h(0)\ncnot(0,1)\nmeasure(0)\nmeasure(1)",
                qubits_used=2,
            ),
        ]

        ent_tutorial = Tutorial(
            tutorial_id="tut_entanglement_1",
            title="Introduction to Quantum Entanglement",
            level=TutorialLevel.INTERMEDIATE,
            concept=ConceptType.ENTANGLEMENT,
            steps=ent_steps,
            completion_time_min=25,
        )
        self.tutorials[ent_tutorial.tutorial_id] = ent_tutorial

    def get_tutorial(self, tutorial_id: str) -> Optional[Tutorial]:
        """Get a tutorial by ID."""
        return self.tutorials.get(tutorial_id)

    def list_tutorials(self, level: Optional[TutorialLevel] = None,
                     concept: Optional[ConceptType] = None) -> List[Dict[str, Any]]:
        """List available tutorials."""
        result = []
        for tut in self.tutorials.values():
            if level and tut.level != level:
                continue
            if concept and tut.concept != concept:
                continue
            result.append(tut.to_dict())
        return result

    def search_tutorials(self, query: str) -> List[Tutorial]:
        """Search tutorials by keyword."""
        query = query.lower()
        result = []
        for tut in self.tutorials.values():
            if query in tut.title.lower() or query in tut.concept.value:
                result.append(tut)
        return result

    def execute_step_code(self, tutorial_id: str, step_index: int) -> Dict[str, Any]:
        """Execute code for a tutorial step and return quantum state."""
        tut = self.get_tutorial(tutorial_id)
        if not tut:
            return {'error': 'Tutorial not found'}

        state = tut.build_quantum_state(step_index)

        # Return state information
        probs = np.abs(state) ** 2
        active_states = [(i, probs[i]) for i in range(len(state)) if probs[i] > 0.01]

        return {
            'state_vector': state[:8].tolist(),  # Limit output
            'probabilities': {format(i, f'0{tut.steps[step_index].qubits_used}b'): p
                                for i, p in active_states},
            'num_qubits': tut.steps[step_index].qubits_used,
        }

    def get_concept(self, concept_id: str) -> Optional[QuantumConcept]:
        """Get a concept by ID."""
        return self.concepts.get(concept_id)

    def list_concepts(self, level: Optional[TutorialLevel] = None) -> List[Dict[str, Any]]:
        """List available concepts."""
        result = []
        for concept in self.concepts.values():
            if level and concept.level != level:
                continue
            result.append(concept.to_dict())
        return result

    def start_tutorial_for_user(self, user: str, tutorial_id: str) -> Dict[str, Any]:
        """Start a tutorial."""
        tut = self.get_tutorial(tutorial_id)
        if not tut:
            return {'error': 'Tutorial not found'}

        return self.progress_tracker.start_tutorial(user, tutorial_id)

    def complete_step_for_user(self, user: str, tutorial_id: str, step_id: str) -> bool:
        """Complete a step for a user."""
        return self.progress_tracker.complete_step(user, tutorial_id, step_id)

    def complete_tutorial_for_user(self, user: str, tutorial_id: str) -> bool:
        """Complete a tutorial for a user."""
        return self.progress_tracker.complete_tutorial(user, tutorial_id)

    def get_user_progress(self, user: str, tutorial_id: Optional[str] = None) -> Dict[str, Any]:
        """Get user progress."""
        return self.progress_tracker.get_progress(user, tutorial_id)

    def get_education_stats(self) -> Dict[str, Any]:
        """Get education module statistics."""
        stats = self.progress_tracker.get_statistics()
        stats['total_tutorials'] = len(self.tutorials)
        stats['total_concepts'] = len(self.concepts)
        return stats


__all__ = [
    'TutorialLevel',
    'ConceptType',
    'QuantumConcept',
    'TutorialStep',
    'Tutorial',
    'ProgressTracker',
    'QuantumEducation',
]
