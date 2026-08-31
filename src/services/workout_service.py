"""
FitQuest Workout Service
Manages creation, retrieval, and template storage for Workout plans in memory.
"""

import uuid
from typing import Dict, List, Optional
from backend.src.models.exercise_target import ExerciseTarget
from backend.src.models.workout import Workout


class WorkoutService:
    """Service managing Workout template creation and lookup."""

    def __init__(self):
        self._workouts: Dict[str, Workout] = {}
        # Pre-seed standard initial workout for immediate elder use
        default_exercises = [
            ExerciseTarget(exercise="squat", sets=3, reps_per_set=20, points_per_rep=2),
            ExerciseTarget(exercise="pushup", sets=2, reps_per_set=10, points_per_rep=3),
            ExerciseTarget(exercise="jumping_jack", sets=2, reps_per_set=15, points_per_rep=2),
        ]
        default_workout = Workout(
            name="Grandpa's Daily Motivation",
            exercises=default_exercises,
            target_points=100,
            workout_id="default-morning-fitness"
        )
        self._workouts[default_workout.workout_id] = default_workout

    def create_workout(
        self,
        name: str,
        exercises: List[ExerciseTarget],
        target_points: int = 100,
        workout_id: Optional[str] = None
    ) -> Workout:
        """
        Create and register a new Workout template.
        """
        wid = workout_id or str(uuid.uuid4())
        workout = Workout(name=name, exercises=exercises, target_points=target_points, workout_id=wid)
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


# Shared singleton instance
shared_workout_service = WorkoutService()
