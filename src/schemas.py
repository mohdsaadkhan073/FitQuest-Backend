"""
FitQuest Pydantic Request & Response Schemas
Provides data validation and serialization models for the FastAPI REST API layer.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExerciseTargetSchema(BaseModel):
    """Schema for exercise target configuration in a workout plan."""
    exercise: str = Field(..., description="Exercise identifier: 'squat', 'pushup', 'jumping_jack'")
    sets: int = Field(..., gt=0, description="Number of sets required")
    reps_per_set: int = Field(..., gt=0, description="Repetitions required per set")
    points_per_rep: int = Field(1, ge=0, description="Points awarded per valid repetition")
    status: str = Field("pending", description="Status: 'pending', 'in_progress', 'completed'")


class CreateWorkoutSchema(BaseModel):
    """Schema for creating a new workout plan."""
    name: str = Field(..., min_length=1, description="Workout name")
    exercises: List[ExerciseTargetSchema] = Field(..., min_length=1, description="List of exercise targets")
    target_points: int = Field(100, gt=0, description="Target score required for completion")
    is_active: bool = Field(True, description="Whether to make this the active workout")


class UpdateWorkoutSchema(BaseModel):
    """Schema for updating an existing workout plan."""
    name: Optional[str] = Field(None, min_length=1, description="Workout name")
    exercises: Optional[List[ExerciseTargetSchema]] = Field(None, min_length=1, description="List of exercise targets")
    target_points: Optional[int] = Field(None, gt=0, description="Target score required for completion")
    is_active: Optional[bool] = Field(None, description="Whether to make this the active workout")


class WorkoutSchema(BaseModel):
    """Schema for returning workout details."""
    workout_id: str
    name: str
    exercises: List[ExerciseTargetSchema]
    target_points: int
    is_active: bool = False


class SetActiveWorkoutSchema(BaseModel):
    """Schema for setting the active workout."""
    workout_id: str = Field(..., description="ID of workout to activate")


class ElderProfileSchema(BaseModel):
    """Schema for returning elder profile and persistent points state."""
    profile_id: str
    elder_name: str
    age: int
    current_points: int
    total_lifetime_points: int
    target_points: int
    streak_days: int
    reset_schedule: str = Field("custom", description="'daily', 'weekly', 'monthly', or 'custom'")
    last_points_reset_at: str
    last_workout_date: str
    reward_unlocked: bool
    active_workout_id: Optional[str] = None
    active_workout_name: Optional[str] = None
    completed_exercises: List[str] = Field(default_factory=list)


class UpdateElderProfileSchema(BaseModel):
    """Schema for updating elder profile details and reset policy."""
    elder_name: Optional[str] = Field(None, min_length=1)
    age: Optional[int] = Field(None, gt=0)
    reset_schedule: Optional[str] = Field(None, description="'daily', 'weekly', 'monthly', or 'custom'")
    target_points: Optional[int] = Field(None, gt=0)
    active_workout_id: Optional[str] = Field(None)
    active_workout_name: Optional[str] = Field(None)
    completed_exercises: Optional[List[str]] = Field(None)


class ResetPointsResponseSchema(BaseModel):
    """Schema for manual points reset response."""
    status: str = "reset"
    current_points: int = 0
    last_points_reset_at: str
    message: str


class CreateSessionSchema(BaseModel):
    """Schema for starting a new workout session."""
    workout_id: Optional[str] = Field(None, description="ID of workout plan to start")


class ExerciseResultSchema(BaseModel):
    """Schema for receiving model ExerciseResult payloads."""
    exercise: str = Field(..., description="Exercise identifier")
    reps: int = Field(..., ge=0, description="Total valid repetitions detected by model")
    state: str = Field("INITIALIZING", description="Current movement state, e.g. 'UP', 'DOWN', 'OPEN'")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Landmark confidence score")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Joint angle metrics")
    feedback: str = Field("", description="Real-time form feedback message")


class SwitchExerciseSchema(BaseModel):
    """Schema for switching active exercise mode."""
    exercise: str = Field(..., description="Exercise identifier to switch to")


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
    completed_exercises: List[str] = Field(default_factory=list)


class DayExerciseHistorySchema(BaseModel):
    """Schema for single exercise progress on a given day."""
    exercise: str
    reps: int
    sets: int = 1
    points: int = 0


class DayHistorySchema(BaseModel):
    """Schema for day-wise aggregated workout progress."""
    date: str
    display_date: str
    total_reps: int
    total_points: int
    sessions_count: int = 0
    exercises: List[DayExerciseHistorySchema] = []


class RecordHistoryPayloadSchema(BaseModel):
    """Schema for recording completed workout sets/exercises."""
    session_id: str
    workout_id: str
    workout_name: str
    exercise: str
    reps: int
    sets: int = 1
    points: int = 0


class HealthCheckSchema(BaseModel):
    """Schema for system health check endpoint."""
    status: str = "ok"
    service: str = "FitQuest Backend API"
    version: str = "1.0.0"
