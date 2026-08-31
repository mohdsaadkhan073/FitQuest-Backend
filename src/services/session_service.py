"""
FitQuest Session Service
Manages active workout sessions, advances set/exercise progress, calculates incremental scoring,
persists progress history, syncs persistent elder points, and processes model ExerciseResult objects.
"""

from typing import Any, Dict, List, Optional, Union
from backend.src.models.workout import Workout
from backend.src.models.workout_session import WorkoutSession
from backend.src.services.scoring_service import ScoringService
from backend.src.db.history_repo import history_repo
from backend.src.db.elder_repo import elder_repo


def normalize_ex_name(name: str) -> str:
    """Normalize exercise string to canonical name."""
    if not name:
        return "squat"
    n = name.lower().strip().replace("-", "_").replace(" ", "_")
    if n in ["squats", "squat"]:
        return "squat"
    if n in ["pushups", "pushup", "push_ups", "push_up"]:
        return "pushup"
    if n in ["jumping_jacks", "jumping_jack", "jumpingjacks", "jumpingjack"]:
        return "jumping_jack"
    return n


class SessionService:
    """Service managing active WorkoutSession progression and integration with ExerciseResult payloads."""

    def __init__(self, scoring_service: Optional[ScoringService] = None):
        self.scoring_service = scoring_service or ScoringService()
        self._sessions: Dict[str, WorkoutSession] = {}

    def start_session(self, workout: Workout) -> WorkoutSession:
        """
        Initialize and register a new active WorkoutSession, synced with elder persistent points.
        """
        profile = elder_repo.get_profile()
        session = WorkoutSession(
            workout=workout,
            current_points=profile.get("current_points", 0)
        )
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WorkoutSession]:
        """
        Retrieve session by session_id and ensure points are fresh from elder_repo.
        """
        session = self._sessions.get(session_id)
        if session:
            profile = elder_repo.get_profile()
            db_points = profile.get("current_points", 0)
            if db_points > session.current_points:
                session.current_points = db_points
        return session

    def list_sessions(self) -> List[WorkoutSession]:
        """
        Return list of all active or stored workout sessions with refreshed points.
        """
        profile = elder_repo.get_profile()
        db_points = profile.get("current_points", 0)
        for session in self._sessions.values():
            if db_points > session.current_points:
                session.current_points = db_points
        return list(self._sessions.values())

    def switch_exercise(self, session_id: str, exercise_name: str) -> Optional[WorkoutSession]:
        """
        Switch the active exercise target in a session by target_id or exercise name.
        """
        session = self.get_session(session_id)
        if not session:
            return None

        clean_id = exercise_name.lower().strip()
        try:
            new_index = next(
                i for i, ex in enumerate(session.workout.exercises)
                if ex.target_id.lower() == clean_id or normalize_ex_name(ex.exercise) == normalize_ex_name(clean_id)
            )
        except StopIteration:
            return None

        session.current_exercise_index = new_index
        session.current_set_index = 0

        # Reset model rep tracking for this exercise to allow fresh counting
        clean_ex_name = session.workout.exercises[new_index].exercise
        if clean_ex_name in session._last_processed_model_reps:
            session._last_processed_model_reps[clean_ex_name] = 0

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
        Process an ExerciseResult from model or manual simulator, update points & history.
        """
        session = self.get_session(session_id)
        if not session:
            # Create session for active workout automatically
            from backend.src.db.workout_repo import workout_repo
            active_w = workout_repo.get_active_workout()
            session = self.start_session(Workout.from_dict(active_w))

        if isinstance(result_data, dict):
            raw_ex = result_data.get("exercise", "squat")
            model_rep_count = int(result_data.get("reps", 0))
        else:
            raw_ex = getattr(result_data, "exercise", "squat")
            model_rep_count = int(getattr(result_data, "reps", 0))

        exercise_name = normalize_ex_name(raw_ex)
        active_target = session.current_exercise_target

        if not active_target or normalize_ex_name(active_target.exercise) != exercise_name:
            try:
                matching_idx = next(
                    i for i, ex in enumerate(session.workout.exercises)
                    if normalize_ex_name(ex.exercise) == exercise_name
                )
                session.current_exercise_index = matching_idx
                session.current_set_index = 0
                active_target = session.current_exercise_target
            except StopIteration:
                pass

        if not active_target or normalize_ex_name(active_target.exercise) != exercise_name:
            return session

        # 1. Monotonic Rep Delta Filtering
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
                
                # Calculate and accumulate score
                pts_rate = max(1, getattr(active_target, 'points_per_rep', 2))
                earned_points = accepted * pts_rate
                
                # Update persistent profile and session points
                updated_profile = elder_repo.add_points(earned_points)
                session.current_points = updated_profile.get("current_points", session.current_points + earned_points)

                # Persist progress into history
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
                    elder_repo.mark_exercise_completed(exercise_name, getattr(active_target, 'target_id', None))
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
