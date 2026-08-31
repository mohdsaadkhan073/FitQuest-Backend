"""
FitQuest Workout Service
Manages creation, retrieval, update, deletion, and active template selection for Workout plans using WorkoutRepository.
"""

import uuid
from typing import Any, Dict, List, Optional
from backend.src.models.exercise_target import ExerciseTarget
from backend.src.models.workout import Workout
from backend.src.db.workout_repo import workout_repo
from backend.src.db.elder_repo import elder_repo


def _dict_to_workout(data: Dict[str, Any]) -> Workout:
    """Convert database dict to Workout domain model."""
    targets = [
        ExerciseTarget(
            exercise=ex["exercise"],
            sets=int(ex["sets"]),
            reps_per_set=int(ex["reps_per_set"]),
            points_per_rep=int(ex.get("points_per_rep", 1))
        )
        for ex in data.get("exercises", [])
    ]
    return Workout(
        name=data.get("name", "Custom Workout"),
        exercises=targets,
        target_points=int(data.get("target_points", 100)),
        workout_id=data.get("workout_id", str(uuid.uuid4()))
    )


class WorkoutService:
    """Service managing Workout template creation, lookup, updates, and persistence."""

    def create_workout(
        self,
        name: str,
        exercises: List[ExerciseTarget],
        target_points: int = 100,
        workout_id: Optional[str] = None,
        is_active: bool = True
    ) -> Workout:
        """Create, register, and persist a new Workout template in MongoDB."""
        wid = workout_id or str(uuid.uuid4())
        workout = Workout(name=name, exercises=exercises, target_points=target_points, workout_id=wid)
        doc = workout.to_dict()
        doc["is_active"] = is_active

        workout_repo.create_workout(doc)

        if is_active:
            elder_repo.update_profile(
                active_workout_id=wid,
                active_workout_name=name,
                target_points=target_points
            )

        return workout

    def get_workout(self, workout_id: str) -> Optional[Workout]:
        """Retrieve workout from MongoDB by ID."""
        doc = workout_repo.get_workout(workout_id)
        if doc:
            return _dict_to_workout(doc)
        return None

    def get_active_workout(self) -> Workout:
        """Retrieve currently active workout template from MongoDB."""
        doc = workout_repo.get_active_workout()
        return _dict_to_workout(doc)

    def set_active_workout(self, workout_id: str) -> Optional[Workout]:
        """Set workout as active."""
        doc = workout_repo.set_active_workout(workout_id)
        if doc:
            workout = _dict_to_workout(doc)
            elder_repo.update_profile(
                active_workout_id=workout.workout_id,
                active_workout_name=workout.name,
                target_points=workout.target_points
            )
            return workout
        return None

    def update_workout(
        self,
        workout_id: str,
        name: Optional[str] = None,
        exercises: Optional[List[ExerciseTarget]] = None,
        target_points: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Workout]:
        """Update existing workout template in MongoDB."""
        update_data: Dict[str, Any] = {}
        if name is not None:
            update_data["name"] = name
        if exercises is not None:
            update_data["exercises"] = [ex.to_dict() for ex in exercises]
        if target_points is not None:
            update_data["target_points"] = target_points
        if is_active is not None:
            update_data["is_active"] = is_active

        doc = workout_repo.update_workout(workout_id, update_data)
        if doc:
            workout = _dict_to_workout(doc)
            if doc.get("is_active", False):
                elder_repo.update_profile(
                    active_workout_id=workout.workout_id,
                    active_workout_name=workout.name,
                    target_points=workout.target_points
                )
            return workout
        return None

    def delete_workout(self, workout_id: str) -> bool:
        """Delete workout template from MongoDB."""
        return workout_repo.delete_workout(workout_id)

    def list_workouts(self) -> List[Workout]:
        """List all registered workout templates from MongoDB."""
        docs = workout_repo.list_workouts()
        return [_dict_to_workout(d) for d in docs]


# Shared singleton instance
shared_workout_service = WorkoutService()
