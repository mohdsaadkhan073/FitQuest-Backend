"""
FitQuest Session Controller
Handles API business logic for WorkoutSession creation, status retrieval, processing ExerciseResult payloads, and set progress.
"""

from fastapi import HTTPException, status

from backend.src.controllers.workout_controller import workout_service
from backend.src.schemas import (
    CreateSessionSchema,
    ExerciseResultSchema,
    SetProgressSchema,
    WorkoutSessionSchema,
)
from backend.src.services.session_service import shared_session_service as session_service


class SessionController:
    """Controller delegating HTTP session requests to SessionService."""

    @staticmethod
    def start_session(payload: CreateSessionSchema) -> WorkoutSessionSchema:
        """Start a new workout session for a given workout_id."""
        workout = workout_service.get_workout(payload.workout_id)
        if not workout:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout with ID '{payload.workout_id}' not found. Create workout first."
            )
        session = session_service.start_session(workout)
        return WorkoutSessionSchema(**session.to_dict())

    @staticmethod
    def get_session(session_id: str) -> WorkoutSessionSchema:
        """Retrieve active workout session status."""
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout session with ID '{session_id}' not found."
            )
        return WorkoutSessionSchema(**session.to_dict())

    @staticmethod
    def process_result(session_id: str, payload: ExerciseResultSchema) -> WorkoutSessionSchema:
        """Process an ExerciseResult payload from CV model and update session state."""
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout session with ID '{session_id}' not found."
            )

        updated_session = session_service.process_exercise_result(session_id, payload.model_dump())
        return WorkoutSessionSchema(**updated_session.to_dict())

    @staticmethod
    def get_session_progress(session_id: str) -> SetProgressSchema:
        """Get progress for current active set in session."""
        session = session_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workout session with ID '{session_id}' not found."
            )

        progress = session.current_set_progress
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active set progress available. Workout may be completed."
            )
        return SetProgressSchema(**progress.to_dict())
