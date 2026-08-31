"""
FitQuest Exercise Manager Component
Central manager coordinating active exercise registration, switching, rep resetting, and API dictionary output formatting.
"""

from typing import Any, Dict, List, Optional, Tuple

from backend.model.exercises import (
    BaseExercise,
    ExerciseResult,
    JumpingJackDetector,
    PushUpDetector,
    SquatDetector,
)


class ExerciseManager:
    """Central registry and controller for active exercise tracking."""

    def __init__(self):
        # Register available exercises
        self.exercises: Dict[str, BaseExercise] = {
            "squat": SquatDetector(),
            "pushup": PushUpDetector(),
            "jumping_jack": JumpingJackDetector()
        }
        
        # Default starting exercise
        self.active_name: str = "squat"

    @property
    def current_exercise(self) -> BaseExercise:
        return self.exercises.get(self.active_name, self.exercises["squat"])

    def set_active_exercise(self, name: str) -> bool:
        """
        Switch active exercise by identifier ('squat', 'pushup', 'jumping_jack').
        """
        if not name:
            return False
        clean_name = name.lower().strip()
        if "jump" in clean_name:
            canonical = "jumping_jack"
        elif "push" in clean_name:
            canonical = "pushup"
        elif "squat" in clean_name:
            canonical = "squat"
        else:
            canonical = clean_name

        if canonical in self.exercises:
            self.active_name = canonical
            return True
        return False

    def reset_current_reps(self):
        """Reset rep count for currently active exercise."""
        self.current_exercise.reset()

    def reset_all(self):
        """Reset rep counts for all registered exercises."""
        for ex in self.exercises.values():
            ex.reset()

    def process_landmarks(
        self,
        landmarks: Optional[List[Any]],
        image_shape: Tuple[int, int]
    ) -> ExerciseResult:
        """
        Pass frame landmarks to current active exercise detector and return structured result.
        """
        return self.current_exercise.update(landmarks, image_shape)

    def get_registered_exercises(self) -> List[str]:
        """Return list of registered exercise names."""
        return list(self.exercises.keys())
