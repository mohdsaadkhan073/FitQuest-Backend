"""
FitQuest Session Service
Manages active workout sessions, advances set/exercise progress, calculates incremental scoring, and processes model ExerciseResult objects.
"""

from typing import Any, Dict, Optional, Union
from backend.src.models.workout import Workout
from backend.src.models.workout_session import WorkoutSession
from backend.src.services.scoring_service import ScoringService


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

    def process_exercise_result(
        self,
        session_id: str,
        result_data: Union[Any, Dict[str, Any]]
    ) -> WorkoutSession:
        """
        Process an ExerciseResult (or dict) from backend/model and update session progress & points.
        
        :param session_id: Active session ID.
        :param result_data: ExerciseResult dataclass instance or dict.
        :return: Updated WorkoutSession instance.
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
            # Exercise result doesn't match active exercise target; ignore or record for current exercise tracker
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
                
                remaining_delta -= accepted

            # Check if current set has reached target reps
            if active_progress.is_complete:
                session.completed_sets += 1
                session.current_set_index += 1

                # Check if all sets for current exercise are completed
                if session.current_set_index >= active_target.sets:
                    session.current_exercise_index += 1
                    session.current_set_index = 0

                    # Check if all exercises in workout are completed
                    if session.current_exercise_index >= len(session.workout.exercises):
                        session.is_completed = True
                        break

        return session


# Shared singleton instance
shared_session_service = SessionService()
