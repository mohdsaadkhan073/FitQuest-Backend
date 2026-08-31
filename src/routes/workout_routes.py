"""
FitQuest Workout API Routes
FastAPI APIRouter for /api/v1/workouts endpoints.
"""

from typing import List
from fastapi import APIRouter, status

from backend.src.controllers.workout_controller import WorkoutController
from backend.src.schemas import CreateWorkoutSchema, WorkoutSchema

router = APIRouter(prefix="/api/v1/workouts", tags=["Workouts"])


@router.post("", response_model=WorkoutSchema, status_code=status.HTTP_201_CREATED)
def create_workout(payload: CreateWorkoutSchema):
    """Create a new workout plan."""
    return WorkoutController.create_workout(payload)


@router.get("", response_model=List[WorkoutSchema])
def list_workouts():
    """List all available workout plans."""
    return WorkoutController.list_workouts()


@router.get("/{workout_id}", response_model=WorkoutSchema)
def get_workout(workout_id: str):
    """Retrieve workout plan details by ID."""
    return WorkoutController.get_workout(workout_id)
