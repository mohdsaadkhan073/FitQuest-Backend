"""
FitQuest Workout Session Domain Model
Represents an active workout session, tracking active exercise, set progression, accumulated score, and target completion status.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from backend.src.models.exercise_target import ExerciseTarget
from backend.src.models.progress import SetProgress
from backend.src.models.workout import Workout


@dataclass
class WorkoutSession:
    """Active session state tracking workout progress, sets, points, and target status."""
    workout: Workout
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_exercise_index: int = 0
    current_set_index: int = 0
    completed_sets: int = 0
    total_valid_reps: int = 0
    current_points: int = 0
    is_completed: bool = False
    
    # Active set progress trackers mapped by (exercise_index, set_index)
    _set_trackers: Dict[str, SetProgress] = field(default_factory=dict, repr=False)
    
    # Monotonic rep counter tracker mapped by exercise name
    _last_processed_model_reps: Dict[str, int] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._initialize_set_trackers()

    def _initialize_set_trackers(self):
        """Initialize SetProgress objects for all exercise targets and sets."""
        for ex_idx, ex_target in enumerate(self.workout.exercises):
            for s_idx in range(ex_target.sets):
                key = f"{ex_idx}_{s_idx}"
                if key not in self._set_trackers:
                    self._set_trackers[key] = SetProgress(
                        set_number=s_idx + 1,
                        target_reps=ex_target.reps_per_set,
                        completed_reps=0
                    )

    @property
    def current_exercise_target(self) -> Optional[ExerciseTarget]:
        """Get active ExerciseTarget."""
        if 0 <= self.current_exercise_index < len(self.workout.exercises):
            return self.workout.exercises[self.current_exercise_index]
        return None

    @property
    def current_set_progress(self) -> Optional[SetProgress]:
        """Get active SetProgress."""
        key = f"{self.current_exercise_index}_{self.current_set_index}"
        return self._set_trackers.get(key)

    @property
    def target_reached(self) -> bool:
        """
        True if current accumulated points meet or exceed the workout target points.
        Evaluated using current_points >= target_points (>= comparison).
        """
        return self.current_points >= self.workout.target_points

    def to_dict(self) -> Dict[str, Any]:
        """Serialize WorkoutSession state to standard dictionary."""
        active_target = self.current_exercise_target
        active_progress = self.current_set_progress

        return {
            "session_id": self.session_id,
            "workout_id": self.workout.workout_id,
            "workout_name": self.workout.name,
            "current_exercise": active_target.exercise if active_target else None,
            "current_exercise_index": self.current_exercise_index,
            "current_set": (self.current_set_index + 1) if active_target else 0,
            "total_sets_in_exercise": active_target.sets if active_target else 0,
            "current_set_progress": active_progress.to_dict() if active_progress else None,
            "completed_sets": self.completed_sets,
            "total_valid_reps": self.total_valid_reps,
            "current_points": self.current_points,
            "target_points": self.workout.target_points,
            "target_reached": self.target_reached,
            "is_completed": self.is_completed
        }
