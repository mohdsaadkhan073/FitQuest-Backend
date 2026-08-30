"""
FitQuest Base Exercise Interface
Defines the ExerciseResult data transfer object and BaseExercise abstract class for exercise detection logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExerciseResult:
    """Structured result returned by exercise detectors for consumption by API/downstream components."""
    exercise: str                     # Exercise identifier, e.g. "squat", "pushup", "jumping_jack"
    reps: int                         # Total valid repetitions completed in session
    state: str                        # Current state, e.g. "UP", "DOWN", "OPEN", "CLOSED", "NO_POSE"
    confidence: float                 # Confidence score (0.0 to 1.0) based on landmark visibility
    metrics: Dict[str, float] = field(default_factory=dict)  # Key numerical metrics (e.g. joint angles)
    feedback: str = ""                # Form feedback or state instruction message

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExerciseResult to standard serializable dictionary structure."""
        return {
            "exercise": self.exercise,
            "reps": self.reps,
            "state": self.state,
            "confidence": round(self.confidence, 2),
            "metrics": {k: round(v, 1) for k, v in self.metrics.items()},
            "feedback": self.feedback
        }


class BaseExercise(ABC):
    """Abstract Base Class for exercise recognition and rep-counting implementations."""

    def __init__(self, name: str):
        self.name = name
        self.reps: int = 0
        self.state: str = "INITIALIZING"
        self.feedback: str = "Get into starting position"

    @abstractmethod
    def update(
        self,
        landmarks: Optional[List[Any]],
        image_shape: Tuple[int, int]
    ) -> ExerciseResult:
        """
        Process current frame pose landmarks and update exercise state & rep counts.
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset repetition count and state machine to initial clean state."""
        self.reps = 0
        self.state = "INITIALIZING"
        self.feedback = "Get into starting position"

    def get_reps(self) -> int:
        return self.reps

    def get_state(self) -> str:
        return self.state
