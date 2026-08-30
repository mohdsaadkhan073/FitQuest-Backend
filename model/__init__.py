"""
FitQuest Model Package
Provides high-level imports for external Python components.
"""

from backend.model.exercise_manager import ExerciseManager as ExerciseDetector
from backend.model.exercises.base import BaseExercise, ExerciseResult
from backend.model.pose_estimator import PoseEstimator

__all__ = [
    "ExerciseDetector",
    "ExerciseResult",
    "BaseExercise",
    "PoseEstimator",
]
