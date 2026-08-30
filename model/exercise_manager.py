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
        return self.exercises[self.active_name]

    def set_active_exercise(self, name: str) -> bool:
        """
        Switch active exercise by identifier ('squat', 'pushup', 'jumping_jack').
        
        :param name: Exercise key string.
        :return: True if active exercise changed successfully.
        """
        clean_name = name.lower().strip()
        if clean_name in self.exercises:
            self.active_name = clean_name
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
        
        :param landmarks: Pose landmarks from PoseEstimator.
        :param image_shape: (height, width) frame dimension tuple.
        :return: ExerciseResult dataclass.
        """
        return self.current_exercise.update(landmarks, image_shape)

    def get_registered_exercises(self) -> List[str]:
        """Return list of registered exercise names."""
        return list(self.exercises.keys())
