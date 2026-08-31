"""
FitQuest Workout Repository
Handles persistent storage, retrieval, update, and deletion of workout plans in MongoDB with resilient in-memory fallback.
"""

from typing import Any, Dict, List, Optional
from backend.src.db.mongo_client import get_db


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
    """Repository storing and querying workout templates in MongoDB (workouts collection)."""

    def __init__(self):
        self._in_memory_workouts: Dict[str, Dict[str, Any]] = {
            DEFAULT_WORKOUT_DICT["workout_id"]: dict(DEFAULT_WORKOUT_DICT)
        }
        self._active_workout_id: str = DEFAULT_WORKOUT_DICT["workout_id"]

    def _ensure_default_seeded(self):
        """Seed default workout in MongoDB if collection is empty."""
        db = get_db()
        if db is not None:
            try:
                count = db.workouts.count_documents({})
                if count == 0:
                    db.workouts.insert_one(dict(DEFAULT_WORKOUT_DICT))
            except Exception as e:
                print(f"[WorkoutRepository] Seed notice: {e}")

    def list_workouts(self) -> List[Dict[str, Any]]:
        """List all workout templates."""
        self._ensure_default_seeded()
        db = get_db()
        if db is not None:
            try:
                docs = list(db.workouts.find({}, {"_id": 0}))
                if docs:
                    return docs
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB list notice: {e}")

        return list(self._in_memory_workouts.values())

    def get_workout(self, workout_id: str) -> Optional[Dict[str, Any]]:
        """Get workout template by ID."""
        self._ensure_default_seeded()
        db = get_db()
        if db is not None:
            try:
                doc = db.workouts.find_one({"workout_id": workout_id}, {"_id": 0})
                if doc:
                    return doc
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB get notice: {e}")

        return self._in_memory_workouts.get(workout_id)

    def get_active_workout(self) -> Dict[str, Any]:
        """Get currently active workout plan."""
        self._ensure_default_seeded()
        db = get_db()
        if db is not None:
            try:
                doc = db.workouts.find_one({"is_active": True}, {"_id": 0})
                if doc:
                    return doc
                first_doc = db.workouts.find_one({}, {"_id": 0})
                if first_doc:
                    return first_doc
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB active workout notice: {e}")

        if self._active_workout_id in self._in_memory_workouts:
            return self._in_memory_workouts[self._active_workout_id]
        if self._in_memory_workouts:
            return next(iter(self._in_memory_workouts.values()))
        return dict(DEFAULT_WORKOUT_DICT)

    def set_active_workout(self, workout_id: str) -> Optional[Dict[str, Any]]:
        """Mark a specific workout as active and deactivate all others."""
        target = self.get_workout(workout_id)
        if not target:
            return None

        self._active_workout_id = workout_id
        for wid, w in self._in_memory_workouts.items():
            w["is_active"] = (wid == workout_id)

        db = get_db()
        if db is not None:
            try:
                db.workouts.update_many({}, {"$set": {"is_active": False}})
                db.workouts.update_one({"workout_id": workout_id}, {"$set": {"is_active": True}})
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB set active notice: {e}")

        target["is_active"] = True
        return target

    def create_workout(self, workout_data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new workout template into MongoDB."""
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

        self._in_memory_workouts[wid] = dict(clean_doc)

        db = get_db()
        if db is not None:
            try:
                if clean_doc["is_active"]:
                    db.workouts.update_many({}, {"$set": {"is_active": False}})
                db.workouts.replace_one({"workout_id": wid}, dict(clean_doc), upsert=True)
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB create notice: {e}")

        return clean_doc

    def update_workout(self, workout_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update existing workout template in MongoDB."""
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

        db = get_db()
        if db is not None:
            try:
                if existing.get("is_active"):
                    db.workouts.update_many({"workout_id": {"$ne": workout_id}}, {"$set": {"is_active": False}})
                db.workouts.replace_one({"workout_id": workout_id}, dict(existing), upsert=True)
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB update notice: {e}")

        return existing

    def delete_workout(self, workout_id: str) -> bool:
        """Delete workout template from MongoDB."""
        existed = workout_id in self._in_memory_workouts
        if existed:
            del self._in_memory_workouts[workout_id]

        db = get_db()
        if db is not None:
            try:
                res = db.workouts.delete_one({"workout_id": workout_id})
                return res.deleted_count > 0 or existed
            except Exception as e:
                print(f"[WorkoutRepository] MongoDB delete notice: {e}")

        return existed


workout_repo = WorkoutRepository()
