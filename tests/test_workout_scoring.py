"""
Unit Test Suite for FitQuest Backend Workout Management, Set Progress, & Scoring Logic
"""

import sys
import unittest

# Ensure project root is in python path
sys.path.insert(0, ".")

from backend.model.exercises.base import ExerciseResult
from backend.src.models import ExerciseTarget, SetProgress, Workout, WorkoutSession
from backend.src.services import ScoringService, SessionService, WorkoutService


class TestWorkoutScoring(unittest.TestCase):

    def setUp(self):
        self.workout_service = WorkoutService()
        self.session_service = SessionService()

    # 1. Test Creating a Workout
    def test_1_create_workout(self):
        targets = [
            ExerciseTarget(exercise="squat", sets=3, reps_per_set=20, points_per_rep=2),
            ExerciseTarget(exercise="pushup", sets=2, reps_per_set=10, points_per_rep=3),
            ExerciseTarget(exercise="jumping_jack", sets=2, reps_per_set=15, points_per_rep=2)
        ]
        workout = self.workout_service.create_workout(
            name="Morning Fitness",
            exercises=targets,
            target_points=100
        )

        self.assertIsNotNone(workout.workout_id)
        self.assertEqual(workout.name, "Morning Fitness")
        self.assertEqual(len(workout.exercises), 3)
        self.assertEqual(workout.target_points, 100)
        self.assertEqual(workout.exercises[0].exercise, "squat")

    # 2. Test Starting a Workout Session
    def test_2_start_workout_session(self):
        targets = [ExerciseTarget(exercise="squat", sets=3, reps_per_set=20, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Squat Blast", exercises=targets, target_points=50)
        session = self.session_service.start_session(workout)

        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.current_exercise_index, 0)
        self.assertEqual(session.current_set_index, 0)
        self.assertEqual(session.current_points, 0)
        self.assertFalse(session.is_completed)
        self.assertFalse(session.target_reached)

    # 3. Test Completing One Set (0/20 -> 20/20)
    def test_3_complete_one_set(self):
        targets = [ExerciseTarget(exercise="squat", sets=2, reps_per_set=20, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Squat Workout", exercises=targets, target_points=100)
        session = self.session_service.start_session(workout)

        # Simulate model sending 20 squat reps
        res = ExerciseResult(exercise="squat", reps=20, state="UP", confidence=0.95)
        updated_session = self.session_service.process_exercise_result(session.session_id, res)

        self.assertEqual(updated_session.completed_sets, 1)
        self.assertEqual(updated_session.current_set_index, 1)  # Advanced to Set 2
        self.assertEqual(updated_session.total_valid_reps, 20)
        self.assertEqual(updated_session.current_points, 40)    # 20 * 2 = 40 points

    # 4. Test Completing Multiple Sets & Exercises
    def test_4_complete_multiple_sets_and_exercises(self):
        targets = [
            ExerciseTarget(exercise="squat", sets=1, reps_per_set=10, points_per_rep=2),
            ExerciseTarget(exercise="pushup", sets=1, reps_per_set=5, points_per_rep=3)
        ]
        workout = self.workout_service.create_workout(name="Full Workout", exercises=targets, target_points=35)
        session = self.session_service.start_session(workout)

        # 1. Finish Squat Set (10 reps * 2 = 20 points)
        res_squat = ExerciseResult(exercise="squat", reps=10, state="UP", confidence=0.95)
        session = self.session_service.process_exercise_result(session.session_id, res_squat)

        self.assertEqual(session.current_exercise_index, 1)  # Advanced to Pushup
        self.assertEqual(session.current_points, 20)

        # 2. Finish Pushup Set (5 reps * 3 = 15 points)
        res_pushup = ExerciseResult(exercise="pushup", reps=5, state="UP", confidence=0.95)
        session = self.session_service.process_exercise_result(session.session_id, res_pushup)

        self.assertEqual(session.current_points, 35)
        self.assertTrue(session.is_completed)
        self.assertTrue(session.target_reached)

    # 5. Test Handling Partial Sets (15/20 -> 20/20)
    def test_5_partial_sets(self):
        targets = [ExerciseTarget(exercise="squat", sets=1, reps_per_set=20, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Partial Test", exercises=targets, target_points=50)
        session = self.session_service.start_session(workout)

        # Model sends 15 reps
        res1 = ExerciseResult(exercise="squat", reps=15, state="UP", confidence=0.9)
        session = self.session_service.process_exercise_result(session.session_id, res1)

        progress = session.current_set_progress
        self.assertEqual(progress.completed_reps, 15)
        self.assertFalse(progress.is_complete)
        self.assertEqual(session.completed_sets, 0)

        # Model sends 5 more reps (total 20 reps)
        res2 = ExerciseResult(exercise="squat", reps=20, state="UP", confidence=0.9)
        session = self.session_service.process_exercise_result(session.session_id, res2)

        self.assertEqual(session.completed_sets, 1)
        self.assertEqual(session.total_valid_reps, 20)

    # 6. Test Preventing Double-Counting / Monotonic Rep Delta Safety
    def test_6_prevent_double_counting(self):
        targets = [ExerciseTarget(exercise="squat", sets=1, reps_per_set=20, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Safety Test", exercises=targets, target_points=50)
        session = self.session_service.start_session(workout)

        # Send same model result multiple times across frames
        res = ExerciseResult(exercise="squat", reps=5, state="UP", confidence=0.9)
        session = self.session_service.process_exercise_result(session.session_id, res)
        session = self.session_service.process_exercise_result(session.session_id, res)
        session = self.session_service.process_exercise_result(session.session_id, res)

        self.assertEqual(session.total_valid_reps, 5)
        self.assertEqual(session.current_points, 10)  # 5 * 2 = 10, NOT 30

    # 7. Test Correct Points Calculation (10 squats @ 2 = 20, 5 pushups @ 3 = 15 => 35)
    def test_7_correct_points_calculation(self):
        targets = [
            ExerciseTarget(exercise="squat", sets=1, reps_per_set=10, points_per_rep=2),
            ExerciseTarget(exercise="pushup", sets=1, reps_per_set=5, points_per_rep=3)
        ]
        workout = self.workout_service.create_workout(name="Score Test", exercises=targets, target_points=50)
        session = self.session_service.start_session(workout)

        # 10 squats
        self.session_service.process_exercise_result(session.session_id, ExerciseResult("squat", 10, "UP", 0.9))
        # 5 pushups
        self.session_service.process_exercise_result(session.session_id, ExerciseResult("pushup", 5, "UP", 0.9))

        self.assertEqual(session.current_points, 35)

    # 8. Test Target NOT Reached (99 < 100 => false)
    def test_8_target_not_reached(self):
        targets = [ExerciseTarget(exercise="squat", sets=1, reps_per_set=50, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Target Test", exercises=targets, target_points=100)
        session = self.session_service.start_session(workout)

        # Perform 49 squats -> 98 points
        self.session_service.process_exercise_result(session.session_id, ExerciseResult("squat", 49, "UP", 0.9))

        self.assertEqual(session.current_points, 98)
        self.assertFalse(session.target_reached)

    # 9. Test Target EXACTLY Reached (100 >= 100 => true)
    def test_9_target_exactly_reached(self):
        targets = [ExerciseTarget(exercise="squat", sets=1, reps_per_set=50, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Exact Target Test", exercises=targets, target_points=100)
        session = self.session_service.start_session(workout)

        # Perform 50 squats -> 100 points
        self.session_service.process_exercise_result(session.session_id, ExerciseResult("squat", 50, "UP", 0.9))

        self.assertEqual(session.current_points, 100)
        self.assertTrue(session.target_reached)

    # 10. Test Target EXCEEDED (120 >= 100 => true)
    def test_10_target_exceeded(self):
        targets = [ExerciseTarget(exercise="squat", sets=1, reps_per_set=60, points_per_rep=2)]
        workout = self.workout_service.create_workout(name="Exceed Target Test", exercises=targets, target_points=100)
        session = self.session_service.start_session(workout)

        # Perform 60 squats -> 120 points
        self.session_service.process_exercise_result(session.session_id, ExerciseResult("squat", 60, "UP", 0.9))

        self.assertEqual(session.current_points, 120)
        self.assertTrue(session.target_reached)


if __name__ == "__main__":
    unittest.main()
