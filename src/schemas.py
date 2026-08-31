"""
FitQuest Pydantic Request & Response Schemas
Provides data validation and serialization models for the FastAPI REST API layer.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExerciseTargetSchema(BaseModel):
    """Schema for exercise target configuration in a workout plan."""
    exercise: str = Field(..., description="Exercise identifier, e.g. 'squat', 'pushup', 'jumping_jack'")
    sets: int = Field(..., gt=0, description="Number of sets required")
    reps_per_set: int = Field(..., gt=0, description="Repetitions required per set")
    points_per_rep: int = Field(1, ge=0, description="Points awarded per valid repetition")


class CreateWorkoutSchema(BaseModel):
    """Schema for creating a new workout plan."""
    name: str = Field(..., min_length=1, description="Workout name")
    exercises: List[ExerciseTargetSchema] = Field(..., min_length=1, description="List of exercise targets")
    target_points: int = Field(100, gt=0, description="Target score required for completion")


class WorkoutSchema(BaseModel):
    """Schema for returning workout details."""
    workout_id: str
    name: str
    exercises: List[ExerciseTargetSchema]
    target_points: int


class CreateSessionSchema(BaseModel):
    """Schema for starting a new workout session."""
    workout_id: str = Field(..., min_length=1, description="ID of workout plan to start")


class ExerciseResultSchema(BaseModel):
    """Schema for receiving model ExerciseResult payloads."""
    exercise: str = Field(..., description="Exercise identifier")
    reps: int = Field(..., ge=0, description="Total valid repetitions detected by model")
    state: str = Field("INITIALIZING", description="Current movement state, e.g. 'UP', 'DOWN', 'OPEN'")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Landmark confidence score")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Joint angle metrics")
    feedback: str = Field("", description="Real-time form feedback message")


class SetProgressSchema(BaseModel):
    """Schema for reporting set progress."""
    set_number: int
    target_reps: int
    completed_reps: int
    remaining_reps: int
    is_complete: bool


class WorkoutSessionSchema(BaseModel):
    """Schema for returning active workout session status."""
    session_id: str
    workout_id: str
    workout_name: str
    current_exercise: Optional[str]
    current_exercise_index: int
    current_set: int
    total_sets_in_exercise: int
    current_set_progress: Optional[SetProgressSchema]
    completed_sets: int
    total_valid_reps: int
    current_points: int
    target_points: int
    target_reached: bool
    is_completed: bool


class HealthCheckSchema(BaseModel):
    """Schema for system health check endpoint."""
    status: str = "ok"
    service: str = "FitQuest Backend API"
    version: str = "1.0.0"
