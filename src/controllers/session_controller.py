"""
FitQuest Session Controller
Handles API business logic for WorkoutSession creation, status retrieval, processing ExerciseResult payloads,
exercise mode switching, and day-wise progress history retrieval.
"""

from typing import List, Optional
from fastapi import HTTPException, status

from backend.src.controllers.workout_controller import workout_service
from backend.src.models import ExerciseTarget
from backend.src.schemas import (
    CreateSessionSchema,
    ExerciseResultSchema,
    SetProgressSchema,
    WorkoutSessionSchema,
    SwitchExerciseSchema,
    DayHistorySchema,
    RecordHistoryPayloadSchema,
)
from backend.src.services.session_service import shared_session_service as session_service
from backend.src.db.history_repo import history_repo


class SessionController:
    """Controller delegating HTTP session requests to SessionService and HistoryRepository."""

    @staticmethod
    def start_session(payload: CreateSessionSchema) -> WorkoutSessionSchema:
        """Start a new workout session for a given workout_id or current active workout."""
        workout = None
        if payload.workout_id:
            workout = workout_service.get_workout(payload.workout_id)
        if not workout:
            workout = workout_service.get_active_workout()

        session = session_service.start_session(workout)
        return WorkoutSessionSchema(**session.to_dict())

    @staticmethod
    def get_latest_session() -> WorkoutSessionSchema:
        """Get the most recently active workout session."""
        all_sessions = session_service.list_sessions()
        if not all_sessions:
            workout = workout_service.get_active_workout()
            sess = session_service.start_session(workout)
            return WorkoutSessionSchema(**sess.to_dict())
        return WorkoutSessionSchema(**all_sessions[-1].to_dict())

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
    def list_sessions() -> List[WorkoutSessionSchema]:
        """List all active or registered workout sessions."""
        sessions = session_service.list_sessions()
        return [WorkoutSessionSchema(**s.to_dict()) for s in sessions]

    @staticmethod
    def process_result(session_id: str, payload: ExerciseResultSchema) -> WorkoutSessionSchema:
        """Process an ExerciseResult payload from CV model and update session state."""
        session = session_service.get_session(session_id)
        if not session:
            all_sessions = session_service.list_sessions()
            if all_sessions:
                session = all_sessions[-1]
                session_id = session.session_id
            else:
                workout = workout_service.get_active_workout()
                session = session_service.start_session(workout)
                session_id = session.session_id

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

    @staticmethod
    def switch_exercise(session_id: str, payload: SwitchExerciseSchema) -> WorkoutSessionSchema:
        """Switch active exercise in a session to the specified one."""
        session = session_service.switch_exercise(session_id, payload.exercise)
        if not session:
            all_sessions = session_service.list_sessions()
            if all_sessions:
                session = session_service.switch_exercise(all_sessions[-1].session_id, payload.exercise)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to switch to exercise '{payload.exercise}' for session '{session_id}'."
            )
        return WorkoutSessionSchema(**session.to_dict())

    @staticmethod
    def get_daywise_history() -> List[DayHistorySchema]:
        """Retrieve day-wise aggregated workout progress history."""
        history = history_repo.get_daywise_history()
        return [DayHistorySchema(**h) for h in history]

    @staticmethod
    def record_history(payload: RecordHistoryPayloadSchema):
        """Manually record a completed exercise progress into history."""
        record = history_repo.record_progress(
            session_id=payload.session_id,
            workout_id=payload.workout_id,
            workout_name=payload.workout_name,
            exercise=payload.exercise,
            reps=payload.reps,
            sets=payload.sets,
            points=payload.points
        )
        return {"status": "recorded", "data": record}
