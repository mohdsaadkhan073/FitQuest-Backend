"""
FitQuest Squat Recognition Module
Detects body landmarks (hip, knee, ankle), calculates knee angles, and manages state transitions (UP -> DOWN -> UP).
"""

from typing import Any, List, Optional, Tuple

from backend.model.config import SQUAT_CFG
from backend.model.exercises.base import BaseExercise, ExerciseResult
from backend.model.utils import (
    EMASmoother,
    calculate_angle_2d,
    calculate_landmarks_average_confidence,
    get_landmark_coords,
)


class SquatDetector(BaseExercise):
    """Squat exercise detector and rep counter."""

    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self, config=SQUAT_CFG):
        super().__init__(name="squat")
        self.cfg = config
        self.state = "UP"
        self.reps = 0
        self.feedback = "Stand straight to start"
        
        self.left_knee_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)
        self.right_knee_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)

    def reset(self):
        super().reset()
        self.state = "UP"
        self.left_knee_smoother.reset()
        self.right_knee_smoother.reset()

    def update(
        self,
        landmarks: Optional[List[Any]],
        image_shape: Tuple[int, int]
    ) -> ExerciseResult:
        h, w = image_shape

        if not landmarks:
            return ExerciseResult(
                exercise=self.name,
                reps=self.reps,
                state="NO_POSE",
                confidence=0.0,
                metrics={},
                feedback="No body detected in camera view"
            )

        squat_indices = [
            self.LEFT_HIP, self.RIGHT_HIP,
            self.LEFT_KNEE, self.RIGHT_KNEE,
            self.LEFT_ANKLE, self.RIGHT_ANKLE
        ]
        confidence = calculate_landmarks_average_confidence(landmarks, squat_indices)

        if confidence < self.cfg.MIN_VISIBILITY:
            return ExerciseResult(
                exercise=self.name,
                reps=self.reps,
                state="LOW_CONFIDENCE",
                confidence=confidence,
                metrics={},
                feedback="Step back so full body and legs are visible"
            )

        left_hip = get_landmark_coords(landmarks, self.LEFT_HIP, w, h)[:2]
        left_knee = get_landmark_coords(landmarks, self.LEFT_KNEE, w, h)[:2]
        left_ankle = get_landmark_coords(landmarks, self.LEFT_ANKLE, w, h)[:2]

        right_hip = get_landmark_coords(landmarks, self.RIGHT_HIP, w, h)[:2]
        right_knee = get_landmark_coords(landmarks, self.RIGHT_KNEE, w, h)[:2]
        right_ankle = get_landmark_coords(landmarks, self.RIGHT_ANKLE, w, h)[:2]

        raw_left_angle = calculate_angle_2d(left_hip, left_knee, left_ankle)
        raw_right_angle = calculate_angle_2d(right_hip, right_knee, right_ankle)

        smooth_left_angle = self.left_knee_smoother.filter(raw_left_angle)
        smooth_right_angle = self.right_knee_smoother.filter(raw_right_angle)

        # Use effective knee angle (taking the more bent knee or average)
        avg_knee_angle = min(smooth_left_angle, smooth_right_angle)

        if self.state == "UP" or self.state == "INITIALIZING":
            if avg_knee_angle <= self.cfg.DOWN_THRESHOLD:
                self.state = "DOWN"
                self.feedback = "Squat depth achieved! Drive up!"
            else:
                self.feedback = "Lower down into squat"

        elif self.state == "DOWN":
            if avg_knee_angle >= self.cfg.UP_THRESHOLD:
                self.reps += 1
                self.state = "UP"
                self.feedback = "Rep completed! Good job!"
            elif avg_knee_angle > self.cfg.DOWN_THRESHOLD:
                self.feedback = "Push back up to standing"
            else:
                self.feedback = "Hold depth, then stand up"

        return ExerciseResult(
            exercise=self.name,
            reps=self.reps,
            state=self.state,
            confidence=confidence,
            metrics={
                "knee_angle": avg_knee_angle,
                "left_knee_angle": smooth_left_angle,
                "right_knee_angle": smooth_right_angle
            },
            feedback=self.feedback
        )
