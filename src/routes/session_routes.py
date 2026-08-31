"""
FitQuest Session API Routes
FastAPI APIRouter for workout session lifecycle, real-time CV frame updates, exercise switching, and day-wise progress history.
"""

from typing import List
from fastapi import APIRouter, status

from backend.src.controllers.session_controller import SessionController
from backend.src.schemas import (
    CreateSessionSchema,
    ExerciseResultSchema,
    SetProgressSchema,
    WorkoutSessionSchema,
    SwitchExerciseSchema,
    DayHistorySchema,
    RecordHistoryPayloadSchema,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("", response_model=WorkoutSessionSchema, status_code=status.HTTP_201_CREATED)
def start_session(payload: CreateSessionSchema):
    """Start a new workout session for a given workout_id."""
    return SessionController.start_session(payload)


@router.get("", response_model=List[WorkoutSessionSchema])
def list_sessions():
    """Return all stored workout sessions."""
    return SessionController.list_sessions()


@router.get("/active/latest", response_model=WorkoutSessionSchema)
def get_latest_session():
    """Retrieve the most recently active workout session."""
    return SessionController.get_latest_session()


@router.get("/history/daywise", response_model=List[DayHistorySchema])
def get_daywise_history():
    """Get day-wise aggregated workout progress history."""
    return SessionController.get_daywise_history()


@router.post("/history/record", status_code=status.HTTP_201_CREATED)
def record_history(payload: RecordHistoryPayloadSchema):
    """Record an exercise milestone into persistent history."""
    return SessionController.record_history(payload)


@router.get("/{session_id}", response_model=WorkoutSessionSchema)
def get_session(session_id: str):
    """Retrieve active session status."""
    return SessionController.get_session(session_id)


@router.post("/{session_id}/process-result", response_model=WorkoutSessionSchema)
def process_result(session_id: str, payload: ExerciseResultSchema):
    """Process an ExerciseResult payload from CV model and update session state."""
    return SessionController.process_result(session_id, payload)


@router.get("/{session_id}/progress", response_model=SetProgressSchema)
def get_session_progress(session_id: str):
    """Get active set progress details for session."""
    return SessionController.get_session_progress(session_id)


@router.post("/{session_id}/switch-exercise", response_model=WorkoutSessionSchema)
def switch_exercise(session_id: str, payload: SwitchExerciseSchema):
    """Switch the active exercise detection mode for this session."""
    return SessionController.switch_exercise(session_id, payload)
