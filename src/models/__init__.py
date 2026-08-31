"""
FitQuest Models Package
Provides domain data models for ExerciseTarget, Workout, SetProgress, and WorkoutSession.
"""

from backend.src.models.exercise_target import ExerciseTarget
from backend.src.models.progress import SetProgress
from backend.src.models.workout import Workout
from backend.src.models.workout_session import WorkoutSession

__all__ = [
    "ExerciseTarget",
    "Workout",
    "SetProgress",
    "WorkoutSession",
]
