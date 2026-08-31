"""
FitQuest Workout Controller
Handles API business logic for Workout creation, retrieval, updates, deletion, and listing using WorkoutService.
"""

from typing import List, Optional
from fastapi import HTTPException, status

from backend.src.models import ExerciseTarget
from backend.src.schemas import (
    CreateWorkoutSchema,
    UpdateWorkoutSchema,
    WorkoutSchema,
    SetActiveWorkoutSchema,
)
from backend.src.services.workout_service import shared_workout_service as workout_service


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
                target_points=payload.target_points,
                is_active=payload.is_active
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
    def get_active_workout() -> WorkoutSchema:
        """Retrieve currently active workout template."""
        workout = workout_service.get_active_workout()
        return WorkoutSchema(**workout.to_dict())

    @staticmethod
    def set_active_workout(payload: SetActiveWorkoutSchema) -> WorkoutSchema:
        """Set a specific workout template as active."""
        workout = workout_service.set_active_workout(payload.workout_id)
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID '{payload.workout_id}' not found"
            )
        return WorkoutSchema(**workout.to_dict())

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

    @staticmethod
    def update_workout(workout_id: str, payload: UpdateWorkoutSchema) -> WorkoutSchema:
        """Update an existing workout template."""
        try:
            targets = None
            if payload.exercises is not None:
                targets = [
                    ExerciseTarget(
                        exercise=ex.exercise,
                        sets=ex.sets,
                        reps_per_set=ex.reps_per_set,
                        points_per_rep=ex.points_per_rep
                    )
                    for ex in payload.exercises
                ]

            workout = workout_service.update_workout(
                workout_id=workout_id,
                name=payload.name,
                exercises=targets,
                target_points=payload.target_points,
                is_active=payload.is_active
            )
            if not workout:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workout with ID '{workout_id}' not found"
                )
            return WorkoutSchema(**workout.to_dict())
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    @staticmethod
    def delete_workout(workout_id: str) -> dict:
        """Delete a workout template by ID."""
        success = workout_service.delete_workout(workout_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID '{workout_id}' not found"
            )
        return {"status": "deleted", "workout_id": workout_id}
