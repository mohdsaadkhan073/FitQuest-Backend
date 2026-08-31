"""
Unit & Integration Test Suite for FitQuest FastAPI Endpoints
"""

import sys
import unittest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, ".")

from backend.src.app import app


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "FitQuest Backend API")

    def test_02_create_workout(self):
        payload = {
            "name": "API Morning Routine",
            "exercises": [
                {"exercise": "squat", "sets": 2, "reps_per_set": 10, "points_per_rep": 2},
                {"exercise": "pushup", "sets": 1, "reps_per_set": 5, "points_per_rep": 3}
            ],
            "target_points": 50
        }
        response = self.client.post("/api/v1/workouts", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn("workout_id", data)
        self.assertEqual(data["name"], "API Morning Routine")
        self.assertEqual(len(data["exercises"]), 2)

    def test_03_list_and_get_workout(self):
        # 1. Create a workout
        create_res = self.client.post("/api/v1/workouts", json={
            "name": "Lookup Workout",
            "exercises": [{"exercise": "jumping_jack", "sets": 1, "reps_per_set": 15, "points_per_rep": 2}],
            "target_points": 30
        })
        workout_id = create_res.json()["workout_id"]

        # 2. List workouts
        list_res = self.client.get("/api/v1/workouts")
        self.assertEqual(list_res.status_code, 200)
        workouts = list_res.json()
        self.assertTrue(any(w["workout_id"] == workout_id for w in workouts))

        # 3. Get workout by ID
        get_res = self.client.get(f"/api/v1/workouts/{workout_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "Lookup Workout")

    def test_04_get_workout_404(self):
        response = self.client.get("/api/v1/workouts/invalid-id-12345")
        self.assertEqual(response.status_code, 404)

    def test_05_session_lifecycle_and_model_processing(self):
        # 1. Create workout
        w_res = self.client.post("/api/v1/workouts", json={
            "name": "Session Test Workout",
            "exercises": [{"exercise": "squat", "sets": 1, "reps_per_set": 10, "points_per_rep": 2}],
            "target_points": 20
        })
        workout_id = w_res.json()["workout_id"]

        # 2. Start session
        s_res = self.client.post("/api/v1/sessions", json={"workout_id": workout_id})
        self.assertEqual(s_res.status_code, 201)
        session_data = s_res.json()
        session_id = session_data["session_id"]
        self.assertEqual(session_data["current_exercise"], "squat")
        self.assertFalse(session_data["target_reached"])

        # 3. Process partial ExerciseResult from model (5 squats -> 10 points)
        res_payload = {
            "exercise": "squat",
            "reps": 5,
            "state": "UP",
            "confidence": 0.95,
            "metrics": {"knee_angle": 155.0},
            "feedback": "Keep going!"
        }
        proc_res1 = self.client.post(f"/api/v1/sessions/{session_id}/process-result", json=res_payload)
        self.assertEqual(proc_res1.status_code, 200)
        proc_data1 = proc_res1.json()
        self.assertEqual(proc_data1["current_points"], 10)
        self.assertFalse(proc_data1["target_reached"])

        # 4. Get active set progress
        prog_res = self.client.get(f"/api/v1/sessions/{session_id}/progress")
        self.assertEqual(prog_res.status_code, 200)
        prog_data = prog_res.json()
        self.assertEqual(prog_data["completed_reps"], 5)
        self.assertEqual(prog_data["remaining_reps"], 5)

        # 5. Process remaining 5 squats (total 10 reps -> 20 points)
        res_payload["reps"] = 10
        proc_res2 = self.client.post(f"/api/v1/sessions/{session_id}/process-result", json=res_payload)
        self.assertEqual(proc_res2.status_code, 200)
        proc_data2 = proc_res2.json()
        self.assertEqual(proc_data2["current_points"], 20)
        self.assertTrue(proc_data2["target_reached"])
        self.assertTrue(proc_data2["is_completed"])

    def test_06_session_404_handling(self):
        response = self.client.get("/api/v1/sessions/invalid-session-999")
        self.assertEqual(response.status_code, 404)

    def test_07_switch_exercise(self):
        # Create multi-exercise workout
        w_res = self.client.post("/api/v1/workouts", json={
            "name": "Multi Exercise Test",
            "exercises": [
                {"exercise": "squat", "sets": 2, "reps_per_set": 10, "points_per_rep": 2},
                {"exercise": "pushup", "sets": 2, "reps_per_set": 10, "points_per_rep": 3},
            ],
            "target_points": 50
        })
        workout_id = w_res.json()["workout_id"]
        s_res = self.client.post("/api/v1/sessions", json={"workout_id": workout_id})
        session_id = s_res.json()["session_id"]

        # Switch to pushup
        switch_res = self.client.post(f"/api/v1/sessions/{session_id}/switch-exercise", json={"exercise": "pushup"})
        self.assertEqual(switch_res.status_code, 200)
        switched_data = switch_res.json()
        self.assertEqual(switched_data["current_exercise"], "pushup")
        self.assertEqual(switched_data["current_exercise_index"], 1)

    def test_08_daywise_history(self):
        res = self.client.get("/api/v1/sessions/history/daywise")
        self.assertEqual(res.status_code, 200)
        history = res.json()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertIn("display_date", history[0])

    def test_09_list_sessions(self):
        res = self.client.get("/api/v1/sessions")
        self.assertEqual(res.status_code, 200)
        sessions = res.json()
        self.assertIsInstance(sessions, list)


if __name__ == "__main__":
    unittest.main()
