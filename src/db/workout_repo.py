"""
FitQuest Workout Repository
Handles persistent storage, retrieval, update, and deletion of workout plans with zero-latency memory cache and async MongoDB synchronization.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from backend.src.db.mongo_client import get_db

_workout_db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="workout_db_worker")

DEFAULT_WORKOUT_DICT: Dict[str, Any] = {
    "workout_id": "default-morning-fitness",
    "name": "Grandpa's Daily Motivation",
    "exercises": [
        {"exercise": "squat", "sets": 3, "reps_per_set": 20, "points_per_rep": 2},
        {"exercise": "pushup", "sets": 2, "reps_per_set": 10, "points_per_rep": 3},
        {"exercise": "jumping_jack", "sets": 2, "reps_per_set": 15, "points_per_rep": 2},
    ],
    "target_points": 100,
    "is_active": True,
}


class WorkoutRepository:
    """Repository storing and querying workout templates with zero-latency in-memory cache."""

    def __init__(self):
        self._in_memory_workouts: Dict[str, Dict[str, Any]] = {
            DEFAULT_WORKOUT_DICT["workout_id"]: dict(DEFAULT_WORKOUT_DICT)
        }
        self._active_workout_id: str = DEFAULT_WORKOUT_DICT["workout_id"]
        _workout_db_executor.submit(self._load_initial_workouts)

    def _load_initial_workouts(self):
        """Initial background load from MongoDB on startup into RAM cache."""
        try:
            db = get_db()
            if db is not None:
                docs = list(db.workouts.find({}, {"_id": 0}))
                if docs:
                    for d in docs:
                        wid = d.get("workout_id")
                        if wid:
                            self._in_memory_workouts[wid] = d
                        if d.get("is_active"):
                            self._active_workout_id = wid
                else:
                    db.workouts.insert_one(dict(DEFAULT_WORKOUT_DICT))
        except Exception as e:
            print(f"[WorkoutRepository] Initial load notice: {e}")

    def list_workouts(self) -> List[Dict[str, Any]]:
        """List all workout templates from RAM (0.001ms)."""
        return list(self._in_memory_workouts.values())

    def get_workout(self, workout_id: str) -> Optional[Dict[str, Any]]:
        """Get workout template by ID from RAM (0.001ms)."""
        return self._in_memory_workouts.get(workout_id)

    def get_active_workout(self) -> Dict[str, Any]:
        """Get currently active workout plan from RAM (0.001ms)."""
        # 1. Check if elder_profile specifies active_workout_id
        from backend.src.db.elder_repo import elder_repo
        prof = elder_repo.get_profile()
        target_id = prof.get("active_workout_id")
        if target_id and target_id in self._in_memory_workouts:
            self._active_workout_id = target_id
            return self._in_memory_workouts[target_id]

        # 2. Check if any workout in memory has is_active == True
        for wid, w in self._in_memory_workouts.items():
            if w.get("is_active"):
                self._active_workout_id = wid
                return w

        # 3. Check self._active_workout_id
        if self._active_workout_id in self._in_memory_workouts:
            return self._in_memory_workouts[self._active_workout_id]

        if self._in_memory_workouts:
            return list(self._in_memory_workouts.values())[-1]
        return dict(DEFAULT_WORKOUT_DICT)

    def _async_mongo_set_active(self, workout_id: str):
        try:
            db = get_db()
            if db is not None:
                db.workouts.update_many({}, {"$set": {"is_active": False}})
                db.workouts.update_one({"workout_id": workout_id}, {"$set": {"is_active": True}})
        except Exception as e:
            print(f"[WorkoutRepository] Async set active notice: {e}")

    def set_active_workout(self, workout_id: str) -> Optional[Dict[str, Any]]:
        """Mark a specific workout as active in RAM and dispatch async write."""
        target = self.get_workout(workout_id)
        if not target:
            return None

        self._active_workout_id = workout_id
        for wid, w in self._in_memory_workouts.items():
            w["is_active"] = (wid == workout_id)

        target["is_active"] = True

        from backend.src.db.elder_repo import elder_repo
        elder_repo.update_profile(
            active_workout_id=workout_id,
            active_workout_name=target.get("name", "Custom Workout"),
            target_points=target.get("target_points", 100)
        )

        _workout_db_executor.submit(self._async_mongo_set_active, workout_id)
        return target

    def _async_mongo_save(self, workout_dict: Dict[str, Any], is_active: bool):
        try:
            db = get_db()
            if db is not None:
                wid = workout_dict.get("workout_id")
                if is_active:
                    db.workouts.update_many({"workout_id": {"$ne": wid}}, {"$set": {"is_active": False}})
                db.workouts.replace_one({"workout_id": wid}, dict(workout_dict), upsert=True)
        except Exception as e:
            print(f"[WorkoutRepository] Async save notice: {e}")

    def create_workout(self, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new workout template in RAM and dispatch async save."""
        wid = workout_data.get("workout_id")
        if not wid:
            import uuid
            wid = str(uuid.uuid4())
            workout_data["workout_id"] = wid

        clean_doc = {
            "workout_id": wid,
            "name": workout_data.get("name", "Custom Workout"),
            "exercises": workout_data.get("exercises", []),
            "target_points": int(workout_data.get("target_points", 100)),
            "is_active": bool(workout_data.get("is_active", True)),
        }

        if clean_doc["is_active"]:
            self._active_workout_id = wid
            for w in self._in_memory_workouts.values():
                w["is_active"] = False

            from backend.src.db.elder_repo import elder_repo
            elder_repo.update_profile(
                active_workout_id=wid,
                active_workout_name=clean_doc["name"],
                target_points=clean_doc["target_points"]
            )

        self._in_memory_workouts[wid] = dict(clean_doc)
        _workout_db_executor.submit(self._async_mongo_save, dict(clean_doc), clean_doc["is_active"])
        return clean_doc

    def update_workout(self, workout_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing workout template in RAM and dispatch async save."""
        existing = self.get_workout(workout_id)
        if not existing:
            return None

        if "name" in update_data and update_data["name"]:
            existing["name"] = str(update_data["name"]).strip()
        if "exercises" in update_data and isinstance(update_data["exercises"], list):
            existing["exercises"] = update_data["exercises"]
        if "target_points" in update_data and update_data["target_points"] is not None:
            existing["target_points"] = max(10, int(update_data["target_points"]))
        if "is_active" in update_data:
            existing["is_active"] = bool(update_data["is_active"])

        self._in_memory_workouts[workout_id] = dict(existing)

        if existing.get("is_active") or self._active_workout_id == workout_id:
            from backend.src.db.elder_repo import elder_repo
            elder_repo.update_profile(
                active_workout_id=workout_id,
                active_workout_name=existing.get("name", "Custom Workout"),
                target_points=existing.get("target_points", 100)
            )

        _workout_db_executor.submit(self._async_mongo_save, dict(existing), existing.get("is_active", False))
        return existing

    def _async_mongo_delete(self, workout_id: str):
        try:
            db = get_db()
            if db is not None:
                db.workouts.delete_one({"workout_id": workout_id})
        except Exception as e:
            print(f"[WorkoutRepository] Async delete notice: {e}")

    def delete_workout(self, workout_id: str) -> bool:
        """Delete workout template from RAM and dispatch async delete."""
        existed = workout_id in self._in_memory_workouts
        if existed:
            del self._in_memory_workouts[workout_id]
            _workout_db_executor.submit(self._async_mongo_delete, workout_id)

        return existed


workout_repo = WorkoutRepository()
