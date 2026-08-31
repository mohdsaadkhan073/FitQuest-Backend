"""
FitQuest Workout Controller
Handles API business logic for Workout creation, retrieval, and listing using WorkoutService.
"""

from typing import List
from fastapi import HTTPException, status

from backend.src.models import ExerciseTarget, Workout
from backend.src.schemas import CreateWorkoutSchema, WorkoutSchema
from backend.src.services import WorkoutService

# Shared global service instance
workout_service = WorkoutService()


class WorkoutController:
    """Controller delegating HTTP requests to WorkoutService."""

    @staticmethod
    def create_workout(payload: CreateWorkoutSchema) -> WorkoutSchema:
        """Create a new workout plan."""
        try:
            targets = [
                ExerciseTarget(
                    exercise=ex.exercise,
                    sets=ex.sets,
                    reps_per_set=ex.reps_per_set,
                    points_per_rep=ex.points_per_rep
                )
                for ex in payload.exercises
            ]
            workout = workout_service.create_workout(
                name=payload.name,
                exercises=targets,
                target_points=payload.target_points
            )
            return WorkoutSchema(**workout.to_dict())
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    @staticmethod
    def list_workouts() -> List[WorkoutSchema]:
        """List all workout templates."""
        workouts = workout_service.list_workouts()
        return [WorkoutSchema(**w.to_dict()) for w in workouts]

    @staticmethod
    def get_workout(workout_id: str) -> WorkoutSchema:
        """Retrieve a specific workout template by ID."""
        workout = workout_service.get_workout(workout_id)
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID '{workout_id}' not found"
            )
        return WorkoutSchema(**workout.to_dict())
