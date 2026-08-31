"""
FitQuest Workout Plan Domain Model
Represents a full workout plan comprising multiple exercise targets with unique target IDs.
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
        if not self.workout_id:
            self.workout_id = str(uuid.uuid4())

    def get_exercise_target(self, identifier: str) -> Optional[ExerciseTarget]:
        """Find ExerciseTarget by target_id or exercise name."""
        clean_id = identifier.lower().strip()
        for target in self.exercises:
            if target.target_id.lower() == clean_id or target.exercise == clean_id:
                return target
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workout":
        """Deserialize Workout from dictionary ensuring each exercise has a unique target_id."""
        raw_exercises = data.get("exercises", [])
        exercises = []
        for ex in raw_exercises:
            if isinstance(ex, dict):
                tid = ex.get("target_id") or f"ex-{uuid.uuid4().hex[:12]}"
                exercises.append(
                    ExerciseTarget(
                        target_id=tid,
                        exercise=ex.get("exercise", "squat"),
                        sets=int(ex.get("sets", 2)),
                        reps_per_set=int(ex.get("reps_per_set", 10)),
                        points_per_rep=int(ex.get("points_per_rep", 2)),
                        status=ex.get("status", "pending")
                    )
                )
            elif isinstance(ex, ExerciseTarget):
                exercises.append(ex)

        return cls(
            workout_id=data.get("workout_id") or str(uuid.uuid4()),
            name=data.get("name", "Custom Workout"),
            exercises=exercises,
            target_points=int(data.get("target_points", 100))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Workout to standard dictionary."""
        return {
            "workout_id": self.workout_id,
            "name": self.name,
            "exercises": [ex.to_dict() for ex in self.exercises],
            "target_points": self.target_points
        }
