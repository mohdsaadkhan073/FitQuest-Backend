"""
FitQuest Workout Service
Manages creation, retrieval, and template storage for Workout plans in memory.
"""

from typing import Dict, List, Optional
from backend.src.models.exercise_target import ExerciseTarget
from backend.src.models.workout import Workout


class WorkoutService:
    """Service managing Workout template creation and lookup."""

    def __init__(self):
        self._workouts: Dict[str, Workout] = {}

    def create_workout(
        self,
        name: str,
        exercises: List[ExerciseTarget],
        target_points: int = 100
    ) -> Workout:
        """
        Create and register a new Workout template.
        """
        workout = Workout(name=name, exercises=exercises, target_points=target_points)
        self._workouts[workout.workout_id] = workout
        return workout

    def get_workout(self, workout_id: str) -> Optional[Workout]:
        """
        Retrieve workout by ID.
        """
        return self._workouts.get(workout_id)

    def list_workouts(self) -> List[Workout]:
        """
        List all registered workout templates.
        """
        return list(self._workouts.values())
