"""
FitQuest Session API Routes
FastAPI APIRouter for /api/v1/sessions endpoints.
"""

from fastapi import APIRouter, status

from backend.src.controllers.session_controller import SessionController
from backend.src.schemas import (
    CreateSessionSchema,
    ExerciseResultSchema,
    SetProgressSchema,
    WorkoutSessionSchema,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.post("", response_model=WorkoutSessionSchema, status_code=status.HTTP_201_CREATED)
def start_session(payload: CreateSessionSchema):
    """Start a new workout session for a given workout_id."""
    return SessionController.start_session(payload)


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
