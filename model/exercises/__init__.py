"""
FitQuest Exercises Package
Exports exercise detectors and base class interface.
"""

from backend.model.exercises.base import BaseExercise, ExerciseResult
from backend.model.exercises.squat import SquatDetector
from backend.model.exercises.pushup import PushUpDetector
from backend.model.exercises.jumping_jack import JumpingJackDetector

__all__ = [
    "BaseExercise",
    "ExerciseResult",
    "SquatDetector",
    "PushUpDetector",
    "JumpingJackDetector",
]
