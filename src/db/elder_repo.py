"""
FitQuest Elder Profile & Points Repository
Handles persistent storage of elder profile, accumulated points, lifetime score, streak,
completed exercise state, and automated/custom points reset schedules with in-memory caching and non-blocking background MongoDB writes.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from backend.src.db.mongo_client import get_db

_db_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="elder_db_worker")

DEFAULT_ELDER_PROFILE: Dict[str, Any] = {
    "profile_id": "elder-default-profile",
    "elder_name": "Grandpa Arthur",
    "age": 78,
    "current_points": 0,
    "total_lifetime_points": 0,
    "target_points": 100,
    "streak_days": 1,
    "reset_schedule": "custom",  # 'daily' (24h) | 'weekly' (7d) | 'monthly' (30d) | 'custom' (manual)
    "last_points_reset_at": datetime.now(timezone.utc).isoformat(),
    "last_workout_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    "reward_unlocked": False,
    "active_workout_id": "default-morning-fitness",
    "active_workout_name": "Grandpa's Daily Motivation",
    "completed_exercises": [],
}


class ElderRepository:
    """Repository managing elder profile, points, streak, completed exercises with zero-latency memory cache."""

    def __init__(self):
        self._in_memory_profile: Dict[str, Any] = dict(DEFAULT_ELDER_PROFILE)
        self._is_seeded = False
        # Dispatch background initial load from MongoDB without blocking module import
        _db_executor.submit(self._load_initial_profile)

    def _load_initial_profile(self):
        """Initial background load from MongoDB on startup into RAM cache."""
        try:
            db = get_db()
            if db is not None:
                doc = db.elder_profile.find_one({}, {"_id": 0})
                if doc:
                    self._in_memory_profile = doc
                    self._is_seeded = True
                else:
                    db.elder_profile.insert_one(dict(DEFAULT_ELDER_PROFILE))
                    self._is_seeded = True
        except Exception as e:
            print(f"[ElderRepository] Initial load notice: {e}")

    def _async_mongo_save(self, profile: Dict[str, Any]):
        """Background thread saving profile to MongoDB without blocking camera stream."""
        try:
            db = get_db()
            if db is not None:
                pid = profile.get("profile_id", "elder-default-profile")
                db.elder_profile.replace_one({"profile_id": pid}, dict(profile), upsert=True)
        except Exception as e:
            print(f"[ElderRepository] MongoDB save notice: {e}")

    def _save_profile_to_db(self, profile: Dict[str, Any]):
        """Persist profile immediately in-memory and dispatch async write to MongoDB."""
        self._in_memory_profile = dict(profile)
        _db_executor.submit(self._async_mongo_save, dict(profile))

    def _check_and_apply_reset_schedule(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if points need to be reset based on the configured reset_schedule.
        """
        schedule = profile.get("reset_schedule", "custom").lower()
        if schedule == "custom":
            return profile

        last_reset_str = profile.get("last_points_reset_at")
        if not last_reset_str:
            return profile

        try:
            if isinstance(last_reset_str, str):
                clean_ts = last_reset_str.replace("Z", "+00:00")
                last_reset_dt = datetime.fromisoformat(clean_ts)
            else:
                last_reset_dt = last_reset_str

            if last_reset_dt.tzinfo is None:
                last_reset_dt = last_reset_dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            elapsed = now - last_reset_dt

            should_reset = False
            if schedule == "daily" and elapsed >= timedelta(hours=24):
                should_reset = True
            elif schedule == "weekly" and elapsed >= timedelta(days=7):
                should_reset = True
            elif schedule == "monthly" and elapsed >= timedelta(days=30):
                should_reset = True

            if should_reset and profile.get("current_points", 0) > 0:
                print(f"[ElderRepository] Auto-resetting points under '{schedule}' policy.")
                profile["current_points"] = 0
                profile["last_points_reset_at"] = now.isoformat()
                profile["reward_unlocked"] = False
                profile["completed_exercises"] = []
                self._save_profile_to_db(profile)

        except Exception as e:
            print(f"[ElderRepository] Reset check notice: {e}")

        return profile

    def get_profile(self) -> Dict[str, Any]:
        """Get elder profile from ultra-fast memory cache (0.001ms)."""
        profile = dict(self._in_memory_profile)

        if "completed_exercises" not in profile:
            profile["completed_exercises"] = []

        profile = self._check_and_apply_reset_schedule(profile)
        
        target = profile.get("target_points", 100)
        curr = profile.get("current_points", 0)
        profile["reward_unlocked"] = (curr >= target and target > 0)
        return profile

    def update_profile(
        self,
        elder_name: Optional[str] = None,
        age: Optional[int] = None,
        reset_schedule: Optional[str] = None,
        target_points: Optional[int] = None,
        active_workout_id: Optional[str] = None,
        active_workout_name: Optional[str] = None,
        completed_exercises: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update elder profile fields and settings in RAM and dispatch async save."""
        profile = self.get_profile()

        if elder_name is not None and elder_name.strip():
            profile["elder_name"] = elder_name.strip()
        if age is not None and age > 0:
            profile["age"] = int(age)
        if reset_schedule is not None and reset_schedule.lower() in ["daily", "weekly", "monthly", "custom"]:
            profile["reset_schedule"] = reset_schedule.lower()
        if target_points is not None and target_points > 0:
            profile["target_points"] = int(target_points)
        if active_workout_id is not None:
            profile["active_workout_id"] = active_workout_id
        if active_workout_name is not None:
            profile["active_workout_name"] = active_workout_name
        if completed_exercises is not None:
            profile["completed_exercises"] = list(set(completed_exercises))

        profile["reward_unlocked"] = (profile["current_points"] >= profile["target_points"])
        self._save_profile_to_db(profile)
        return profile

    def mark_exercise_completed(self, exercise_name: str) -> Dict[str, Any]:
        """Record an exercise as completed in RAM and dispatch async save."""
        profile = self.get_profile()
        clean_name = exercise_name.lower().strip()
        current_list = profile.get("completed_exercises", [])
        if clean_name not in current_list:
            current_list.append(clean_name)
            profile["completed_exercises"] = current_list
            self._save_profile_to_db(profile)
        return profile

    def add_points(self, points: int) -> Dict[str, Any]:
        """Atomically add earned points in RAM and dispatch async save."""
        if points <= 0:
            return self.get_profile()

        profile = self.get_profile()
        profile["current_points"] = profile.get("current_points", 0) + points
        profile["total_lifetime_points"] = profile.get("total_lifetime_points", 0) + points
        
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        last_workout = profile.get("last_workout_date")
        if last_workout != today_str:
            profile["streak_days"] = profile.get("streak_days", 1) + 1
            profile["last_workout_date"] = today_str

        profile["reward_unlocked"] = (profile["current_points"] >= profile.get("target_points", 100))
        self._save_profile_to_db(profile)
        return profile

    def reset_points(self) -> Dict[str, Any]:
        """Manually reset elder current points to 0 in RAM and dispatch async save."""
        profile = self.get_profile()
        profile["current_points"] = 0
        profile["last_points_reset_at"] = datetime.now(timezone.utc).isoformat()
        profile["reward_unlocked"] = False
        profile["completed_exercises"] = []
        self._save_profile_to_db(profile)
        return profile

    def update_target_points(self, target_points: int) -> Dict[str, Any]:
        """Update required target score in RAM and dispatch async save."""
        profile = self.get_profile()
        profile["target_points"] = max(10, int(target_points))
        profile["reward_unlocked"] = (profile["current_points"] >= profile["target_points"])
        self._save_profile_to_db(profile)
        return profile


elder_repo = ElderRepository()
