"""
FitQuest Session Service
Manages active workout sessions, advances set/exercise progress, calculates incremental scoring,
persists progress history to MongoDB/in-memory, and processes model ExerciseResult objects.
"""

from typing import Any, Dict, List, Optional, Union
from backend.src.models.workout import Workout
from backend.src.models.workout_session import WorkoutSession
from backend.src.services.scoring_service import ScoringService
from backend.src.db.history_repo import history_repo


class SessionService:
    """Service managing active WorkoutSession progression and integration with ExerciseResult payloads."""

    def __init__(self, scoring_service: Optional[ScoringService] = None):
        self.scoring_service = scoring_service or ScoringService()
        self._sessions: Dict[str, WorkoutSession] = {}

    def start_session(self, workout: Workout) -> WorkoutSession:
        """
        Initialize and register a new active WorkoutSession.
        """
        session = WorkoutSession(workout=workout)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WorkoutSession]:
        """
        Retrieve session by session_id.
        """
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[WorkoutSession]:
        """
        Return list of all active or stored workout sessions.
        """
        return list(self._sessions.values())

    def switch_exercise(self, session_id: str, exercise_name: str) -> Optional[WorkoutSession]:
        """
        Switch the active exercise target in a session to the specified exercise.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        clean_name = exercise_name.lower().strip()
        try:
            new_index = next(i for i, ex in enumerate(session.workout.exercises) if ex.exercise.lower() == clean_name)
        except StopIteration:
            return None

        session.current_exercise_index = new_index
        session.current_set_index = 0

        # Reset model rep tracking for this exercise to allow fresh monotonic counting
        if clean_name in session._last_processed_model_reps:
            session._last_processed_model_reps[clean_name] = 0

        # Reset set progress tracker for new exercise set 1
        key = f"{new_index}_0"
        if key in session._set_trackers:
            session._set_trackers[key].completed_reps = 0

        return session

    def process_exercise_result(
        self,
        session_id: str,
        result_data: Union[Any, Dict[str, Any]]
    ) -> WorkoutSession:
        """
        Process an ExerciseResult (or dict) from backend/model and update session progress & points.
        """
        session = self.get_session(session_id)
        if not session or session.is_completed:
            return session

        # Normalize ExerciseResult object or dict
        if hasattr(result_data, 'to_dict'):
            payload = result_data.to_dict()
        elif isinstance(result_data, dict):
            payload = result_data
        else:
            raise ValueError(f"Invalid ExerciseResult format: {type(result_data)}")

        exercise_name = payload.get("exercise", "").lower().strip()
        model_rep_count = payload.get("reps", 0)

        # Check if the result corresponds to the currently active exercise target
        active_target = session.current_exercise_target
        if not active_target or active_target.exercise != exercise_name:
            return session

        # 1. Monotonic Rep Delta Filtering (prevents double-counting across frames)
        last_processed = session._last_processed_model_reps.get(exercise_name, 0)
        delta_reps = max(0, model_rep_count - last_processed)

        if delta_reps <= 0:
            return session

        # Update last processed count for this exercise
        session._last_processed_model_reps[exercise_name] = model_rep_count

        # 2. Process incremental reps into active set progress
        remaining_delta = delta_reps

        while remaining_delta > 0 and not session.is_completed:
            active_progress = session.current_set_progress
            if not active_progress:
                break

            accepted = active_progress.add_reps(remaining_delta)
            if accepted > 0:
                # Accumulate valid reps
                session.total_valid_reps += accepted
                
                # Calculate and accumulate score via ScoringService
                earned_points = self.scoring_service.calculate_rep_points(active_target, accepted)
                session.current_points += earned_points

                # Persist progress into MongoDB / in-memory history
                history_repo.record_progress(
                    session_id=session.session_id,
                    workout_id=session.workout.workout_id,
                    workout_name=session.workout.name,
                    exercise=exercise_name,
                    reps=accepted,
                    sets=0,
                    points=earned_points
                )
                
                remaining_delta -= accepted

            # Check if current set has reached target reps
            if active_progress.is_complete:
                session.completed_sets += 1
                session.current_set_index += 1

                # Record completed set in history
                history_repo.record_progress(
                    session_id=session.session_id,
                    workout_id=session.workout.workout_id,
                    workout_name=session.workout.name,
                    exercise=exercise_name,
                    reps=0,
                    sets=1,
                    points=0
                )

                # Check if all sets for current exercise are completed
                if session.current_set_index >= active_target.sets:
                    session.current_exercise_index += 1
                    session.current_set_index = 0

                    # Check if all exercises in workout are completed
                    if session.current_exercise_index >= len(session.workout.exercises):
                        session.is_completed = True
                        break

        return session

    def get_daywise_history(self) -> List[Dict[str, Any]]:
        """Retrieve day-wise progress history."""
        return history_repo.get_daywise_history()


# Shared singleton instance
shared_session_service = SessionService()
