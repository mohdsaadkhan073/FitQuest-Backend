"""
FitQuest Workout API Routes
FastAPI APIRouter for /api/v1/workouts endpoints.
"""

from typing import List
from fastapi import APIRouter, status

from backend.src.controllers.workout_controller import WorkoutController
from backend.src.schemas import (
    CreateWorkoutSchema,
    UpdateWorkoutSchema,
    WorkoutSchema,
    SetActiveWorkoutSchema,
)

router = APIRouter(prefix="/api/v1/workouts", tags=["Workouts"])


@router.post("", response_model=WorkoutSchema, status_code=status.HTTP_201_CREATED)
def create_workout(payload: CreateWorkoutSchema):
    """Create a new workout plan."""
    return WorkoutController.create_workout(payload)


@router.get("", response_model=List[WorkoutSchema])
def list_workouts():
    """List all available workout plans."""
    return WorkoutController.list_workouts()


@router.get("/active/current", response_model=WorkoutSchema)
def get_active_workout():
    """Retrieve currently active workout plan."""
    return WorkoutController.get_active_workout()


@router.post("/active/set", response_model=WorkoutSchema)
def set_active_workout(payload: SetActiveWorkoutSchema):
    """Set active workout plan."""
    return WorkoutController.set_active_workout(payload)


@router.get("/{workout_id}", response_model=WorkoutSchema)
def get_workout(workout_id: str):
    """Retrieve workout plan details by ID."""
    return WorkoutController.get_workout(workout_id)


@router.put("/{workout_id}", response_model=WorkoutSchema)
def update_workout(workout_id: str, payload: UpdateWorkoutSchema):
    """Update an existing workout plan."""
    return WorkoutController.update_workout(workout_id, payload)


@router.delete("/{workout_id}", status_code=status.HTTP_200_OK)
def delete_workout(workout_id: str):
    """Delete a workout plan."""
    return WorkoutController.delete_workout(workout_id)
