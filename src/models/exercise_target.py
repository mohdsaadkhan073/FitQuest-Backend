"""
FitQuest Exercise Target Domain Model
Represents a single exercise target within a workout plan with its own unique primary key ID.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class ExerciseTarget:
    """Target configuration for a specific exercise in a workout with unique target_id."""
    exercise: str             # Exercise identifier, e.g. "squat", "pushup", "jumping_jack"
    sets: int                 # Required number of sets (e.g., 3)
    reps_per_set: int         # Required repetitions per set (e.g., 20)
    points_per_rep: int = 1   # Points awarded per valid completed repetition (e.g., 2)
    target_id: str = field(default_factory=lambda: f"ex-{uuid.uuid4().hex[:12]}")  # Unique ID for each exercise item
    status: str = "pending"   # 'pending' | 'in_progress' | 'completed'

    def __post_init__(self):
        self.exercise = self.exercise.lower().strip()
        if not self.target_id:
            self.target_id = f"ex-{uuid.uuid4().hex[:12]}"
        if self.sets <= 0:
            raise ValueError(f"Sets must be greater than 0, got {self.sets}")
        if self.reps_per_set <= 0:
            raise ValueError(f"Reps per set must be greater than 0, got {self.reps_per_set}")
        if self.points_per_rep < 0:
            raise ValueError(f"Points per rep cannot be negative, got {self.points_per_rep}")

    @property
    def total_target_reps(self) -> int:
        """Total required reps across all sets for this exercise."""
        return self.sets * self.reps_per_set

    @property
    def max_possible_points(self) -> int:
        """Maximum points achievable from this exercise target."""
        return self.total_target_reps * self.points_per_rep

    def to_dict(self) -> Dict[str, Any]:
        """Serialize ExerciseTarget to standard dictionary."""
        return {
            "target_id": self.target_id,
            "exercise": self.exercise,
            "sets": self.sets,
            "reps_per_set": self.reps_per_set,
            "points_per_rep": self.points_per_rep,
            "total_target_reps": self.total_target_reps,
            "max_possible_points": self.max_possible_points,
            "status": self.status
        }
