"""
FitQuest Elder Profile & Points Repository
Handles persistent storage of elder profile, accumulated points, lifetime score, streak,
and automated/custom points reset schedules in MongoDB with resilient in-memory fallback.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from backend.src.db.mongo_client import get_db


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
}


class ElderRepository:
    """Repository managing elder profile, points, streak, and reset schedule policies."""

    def __init__(self):
        self._in_memory_profile: Dict[str, Any] = dict(DEFAULT_ELDER_PROFILE)

    def _ensure_default_seeded(self):
        """Seed default elder profile in MongoDB if collection is empty."""
        db = get_db()
        if db is not None:
            try:
                count = db.elder_profile.count_documents({})
                if count == 0:
                    db.elder_profile.insert_one(dict(DEFAULT_ELDER_PROFILE))
            except Exception as e:
                print(f"[ElderRepository] Seed notice: {e}")

    def _check_and_apply_reset_schedule(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if points need to be reset based on the configured reset_schedule.
        'custom': Never auto-reset.
        'daily': Reset if >= 24 hours have passed since last_points_reset_at.
        'weekly': Reset if >= 7 days have passed.
        'monthly': Reset if >= 30 days have passed.
        """
        schedule = profile.get("reset_schedule", "custom").lower()
        if schedule == "custom":
            # In custom mode, points accumulate indefinitely until manually reset
            return profile

        last_reset_str = profile.get("last_points_reset_at")
        if not last_reset_str:
            return profile

        try:
            # Parse ISO timestamp
            if isinstance(last_reset_str, str):
                # Handle possible trailing Z or timezone offsets
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
                print(f"[ElderRepository] Auto-resetting points under '{schedule}' policy. Elapsed: {elapsed}")
                profile["current_points"] = 0
                profile["last_points_reset_at"] = now.isoformat()
                profile["reward_unlocked"] = False
                self._save_profile_to_db(profile)

        except Exception as e:
            print(f"[ElderRepository] Reset schedule check note: {e}")

        return profile

    def _save_profile_to_db(self, profile: Dict[str, Any]):
        """Persist profile to MongoDB and update in-memory cache."""
        self._in_memory_profile = dict(profile)
        db = get_db()
        if db is not None:
            try:
                pid = profile.get("profile_id", "elder-default-profile")
                db.elder_profile.replace_one({"profile_id": pid}, dict(profile), upsert=True)
            except Exception as e:
                print(f"[ElderRepository] MongoDB save notice: {e}")

    def get_profile(self) -> Dict[str, Any]:
        """Get elder profile and evaluate reset schedule."""
        self._ensure_default_seeded()
        profile = None
        db = get_db()
        if db is not None:
            try:
                doc = db.elder_profile.find_one({}, {"_id": 0})
                if doc:
                    profile = doc
            except Exception as e:
                print(f"[ElderRepository] MongoDB get notice: {e}")

        if not profile:
            profile = dict(self._in_memory_profile)

        # Check and apply reset policy
        profile = self._check_and_apply_reset_schedule(profile)
        
        # Ensure reward_unlocked is accurately evaluated
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
    ) -> Dict[str, Any]:
        """Update elder profile fields and settings without flushing accumulated points."""
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

        profile["reward_unlocked"] = (profile["current_points"] >= profile["target_points"])
        self._save_profile_to_db(profile)
        return profile

    def add_points(self, points: int) -> Dict[str, Any]:
        """Atomically add earned points to elder's persistent profile."""
        if points <= 0:
            return self.get_profile()

        profile = self.get_profile()
        profile["current_points"] = profile.get("current_points", 0) + points
        profile["total_lifetime_points"] = profile.get("total_lifetime_points", 0) + points
        
        # Check streak
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        last_workout = profile.get("last_workout_date")
        if last_workout != today_str:
            profile["streak_days"] = profile.get("streak_days", 1) + 1
            profile["last_workout_date"] = today_str

        profile["reward_unlocked"] = (profile["current_points"] >= profile.get("target_points", 100))
        self._save_profile_to_db(profile)
        return profile

    def reset_points(self) -> Dict[str, Any]:
        """Manually reset elder current points to 0 (for Custom schedule or manual family action)."""
        profile = self.get_profile()
        profile["current_points"] = 0
        profile["last_points_reset_at"] = datetime.now(timezone.utc).isoformat()
        profile["reward_unlocked"] = False
        self._save_profile_to_db(profile)
        return profile

    def update_target_points(self, target_points: int) -> Dict[str, Any]:
        """Update required target score."""
        profile = self.get_profile()
        profile["target_points"] = max(10, int(target_points))
        profile["reward_unlocked"] = (profile["current_points"] >= profile["target_points"])
        self._save_profile_to_db(profile)
        return profile


elder_repo = ElderRepository()
