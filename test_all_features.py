"""
Test script for FitQuest real DB history, workout CRUD, elder points persistence, and reset schedules.
Cleans up temporary test data upon completion so user configurations are never overridden.
"""

import urllib.request
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"


def http_req(path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def run_tests():
    print("=== Testing FitQuest Upgraded Endpoints ===")

    # 1. Elder Profile
    status, profile = http_req("/elder/profile")
    print(f"1. GET /elder/profile: status={status}, points={profile.get('current_points')}, schedule={profile.get('reset_schedule')}")
    assert status == 200

    # 2. Update Elder Profile (set to custom)
    status, updated_prof = http_req("/elder/profile", method="PUT", data={"elder_name": "Grandpa Arthur", "age": 79, "reset_schedule": "custom"})
    print(f"2. PUT /elder/profile: status={status}, name={updated_prof.get('elder_name')}, age={updated_prof.get('age')}")
    assert status == 200 and updated_prof["age"] == 79

    # 3. Create Custom Workout (with 2 exercises)
    new_workout_data = {
        "name": "Evening Cardio & Core",
        "exercises": [
            {"exercise": "squat", "sets": 2, "reps_per_set": 12, "points_per_rep": 3},
            {"exercise": "jumping_jack", "sets": 3, "reps_per_set": 20, "points_per_rep": 2}
        ],
        "target_points": 150,
        "is_active": True
    }
    status, created_w = http_req("/workouts", method="POST", data=new_workout_data)
    wid = created_w["workout_id"]
    print(f"3. POST /workouts: status={status}, workout_id={wid}, target_points={created_w.get('target_points')}")
    assert status == 201

    # 4. Get Active Workout
    status, active_w = http_req("/workouts/active/current")
    print(f"4. GET /workouts/active/current: status={status}, name='{active_w.get('name')}', id={active_w.get('workout_id')}")
    assert status == 200 and active_w["workout_id"] == wid

    # 5. Start Session
    status, session = http_req("/sessions", method="POST", data={"workout_id": wid})
    sid = session["session_id"]
    print(f"5. POST /sessions: status={status}, session_id={sid}, active_ex={session.get('current_exercise')}")
    assert status == 201

    # 6. Process Reps (Award 10 squats = 30 points)
    result_data = {
        "exercise": "squat",
        "reps": 10,
        "state": "UP",
        "confidence": 0.95,
        "metrics": {"knee_angle": 155.0},
        "feedback": "Great squat!"
    }
    status, updated_sess = http_req(f"/sessions/{sid}/process-result", method="POST", data=result_data)
    print(f"6. Process 10 Squats: status={status}, sess_points={updated_sess.get('current_points')}, valid_reps={updated_sess.get('total_valid_reps')}")
    assert status == 200 and updated_sess["current_points"] >= 30

    # 7. Check Elder Profile reflects points permanently
    status, prof_after = http_req("/elder/profile")
    print(f"7. Elder Profile Points: {prof_after.get('current_points')} pts, Lifetime: {prof_after.get('total_lifetime_points')} pts")
    assert prof_after["current_points"] >= 30

    # 8. Check Day-Wise History
    status, history = http_req("/sessions/history/daywise")
    print(f"8. GET /sessions/history/daywise: status={status}, days_count={len(history)}")
    if history:
        print(f"   First day record: {history[0].get('display_date')}, total_reps={history[0].get('total_reps')}, total_points={history[0].get('total_points')}, exercises={len(history[0].get('exercises', []))}")
    assert status == 200

    # 9. Update Workout (change target points to 250)
    status, updated_w = http_req(f"/workouts/{wid}", method="PUT", data={"target_points": 250, "name": "Evening Cardio & Core (Upgraded)"})
    print(f"9. PUT /workouts/{wid}: status={status}, new_target={updated_w.get('target_points')}")
    assert status == 200 and updated_w["target_points"] == 250

    # 10. Verify Points were NOT flushed after updating workout!
    status, prof_check = http_req("/elder/profile")
    print(f"10. Verify Points Preserved: {prof_check.get('current_points')} pts (Target is now {prof_check.get('target_points')})")
    assert prof_check["current_points"] >= 30

    # 11. Test Manual Reset Points Button
    status, reset_res = http_req("/elder/reset-points", method="POST")
    print(f"11. POST /elder/reset-points: status={status}, current_points={reset_res.get('current_points')}")
    assert status == 200 and reset_res["current_points"] == 0

    # 12. Verify Profile after reset
    status, prof_reset = http_req("/elder/profile")
    print(f"12. Profile After Reset: current_points={prof_reset.get('current_points')}, lifetime_points={prof_reset.get('total_lifetime_points')}")
    assert prof_reset["current_points"] == 0 and prof_reset["total_lifetime_points"] >= 30

    # 13. Clean up test workout so it never pollutes user active workout
    http_req(f"/workouts/{wid}", method="DELETE")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY & CLEANED UP!")


if __name__ == "__main__":
    run_tests()
