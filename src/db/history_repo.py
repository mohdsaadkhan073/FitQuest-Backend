"""
FitQuest History Repository
Handles persistence of completed exercise reps, sets, and sessions to MongoDB with resilient in-memory fallback.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.src.db.mongo_client import get_db, is_mongo_connected


class HistoryRepository:
    """Repository storing and querying daily fitness progress history."""

    def __init__(self):
        self._in_memory_records: List[Dict[str, Any]] = []

    def record_progress(
        self,
        session_id: str,
        workout_id: str,
        workout_name: str,
        exercise: str,
        reps: int,
        sets: int = 1,
        points: int = 0,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Record an exercise milestone into history."""
        ts = timestamp or datetime.now(timezone.utc)
        date_str = ts.strftime("%Y-%m-%d")

        record = {
            "session_id": session_id,
            "workout_id": workout_id,
            "workout_name": workout_name,
            "exercise": exercise.lower().strip(),
            "reps": int(reps),
            "sets": int(sets),
            "points": int(points),
            "date": date_str,
            "timestamp": ts.isoformat()
        }

        # Save in-memory
        self._in_memory_records.append(record)

        # Save to MongoDB if connected
        db = get_db()
        if db is not None:
            try:
                db.workout_history.insert_one({**record})
            except Exception as e:
                print(f"[HistoryRepository] MongoDB insert notice: {e}")

        return record

    def get_all_records(self) -> List[Dict[str, Any]]:
        """Retrieve all history records either from MongoDB or in-memory."""
        db = get_db()
        if db is not None:
            try:
                records = list(db.workout_history.find({}, {"_id": 0}))
                if records:
                    return records
            except Exception as e:
                print(f"[HistoryRepository] MongoDB query notice: {e}")

        return list(self._in_memory_records)

    def get_daywise_history(self) -> List[Dict[str, Any]]:
        """
        Group records by calendar day (descending order) with exercise breakdown.
        """
        records = self.get_all_records()
        if not records:
            # Provide sample baseline entries if empty so the UI looks stunning immediately
            today = datetime.now()
            today_str = today.strftime("%Y-%m-%d")
            return [
                {
                    "date": today_str,
                    "display_date": f"Today, {today.strftime('%b %d')}",
                    "total_reps": 0,
                    "total_points": 0,
                    "sessions_count": 0,
                    "exercises": []
                }
            ]

        # Group by date
        grouped: Dict[str, Dict[str, Any]] = {}
        for r in records:
            d = r.get("date") or datetime.now().strftime("%Y-%m-%d")
            if d not in grouped:
                # Format friendly display label
                try:
                    dt = datetime.strptime(d, "%Y-%m-%d")
                    now = datetime.now()
                    if dt.date() == now.date():
                        disp = f"Today, {dt.strftime('%b %d')}"
                    elif (now.date() - dt.date()).days == 1:
                        disp = f"Yesterday, {dt.strftime('%b %d')}"
                    else:
                        disp = dt.strftime("%A, %b %d")
                except Exception:
                    disp = d

                grouped[d] = {
                    "date": d,
                    "display_date": disp,
                    "total_reps": 0,
                    "total_points": 0,
                    "sessions": set(),
                    "exercises_map": {}
                }

            entry = grouped[d]
            entry["total_reps"] += r.get("reps", 0)
            entry["total_points"] += r.get("points", 0)
            if r.get("session_id"):
                entry["sessions"].add(r.get("session_id"))

            ex_name = r.get("exercise", "exercise")
            if ex_name not in entry["exercises_map"]:
                entry["exercises_map"][ex_name] = {
                    "exercise": ex_name,
                    "reps": 0,
                    "sets": 0,
                    "points": 0
                }

            entry["exercises_map"][ex_name]["reps"] += r.get("reps", 0)
            entry["exercises_map"][ex_name]["sets"] += r.get("sets", 1)
            entry["exercises_map"][ex_name]["points"] += r.get("points", 0)

        # Sort dates descending (newest first)
        sorted_dates = sorted(grouped.keys(), reverse=True)
        result = []
        for d in sorted_dates:
            item = grouped[d]
            result.append({
                "date": item["date"],
                "display_date": item["display_date"],
                "total_reps": item["total_reps"],
                "total_points": item["total_points"],
                "sessions_count": len(item["sessions"]),
                "exercises": list(item["exercises_map"].values())
            })

        return result


# Singleton repository instance
history_repo = HistoryRepository()
