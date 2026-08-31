"""
FitQuest Workout Plan Domain Model
Represents a full workout plan comprising multiple exercise targets and a target point goal.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.src.models.exercise_target import ExerciseTarget


@dataclass
class Workout:
    """A full workout plan consisting of one or more exercise targets."""
    name: str
    exercises: List[ExerciseTarget] = field(default_factory=list)
    target_points: int = 100
    workout_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Workout name cannot be empty")
        if not self.exercises:
            raise ValueError("Workout must contain at least one ExerciseTarget")
        if self.target_points <= 0:
            raise ValueError(f"Target points must be greater than 0, got {self.target_points}")

    def get_exercise_target(self, exercise_name: str) -> Optional[ExerciseTarget]:
        """Find ExerciseTarget by exercise name."""
        clean_name = exercise_name.lower().strip()
        for target in self.exercises:
            if target.exercise == clean_name:
                return target
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Workout to standard dictionary."""
        return {
            "workout_id": self.workout_id,
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises],
            "target_points": self.target_points
        }
