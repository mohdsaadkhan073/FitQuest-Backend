"""
FitQuest Push-up Recognition Module
Detects upper-body landmarks (shoulder, elbow, wrist), calculates elbow joint angles, and tracks state transitions.
"""

from typing import Any, List, Optional, Tuple

from backend.model.config import PUSHUP_CFG
from backend.model.exercises.base import BaseExercise, ExerciseResult
from backend.model.utils import (
    EMASmoother,
    calculate_angle_2d,
    calculate_landmarks_average_confidence,
    get_landmark_coords,
)


class PushUpDetector(BaseExercise):
    """Push-up exercise detector and rep counter."""

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24

    def __init__(self, config=PUSHUP_CFG):
        super().__init__(name="pushup")
        self.cfg = config
        self.state = "UP"
        self.reps = 0
        self.feedback = "Get into plank/push-up position"
        
        self.left_elbow_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)
        self.right_elbow_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)

    def reset(self):
        super().reset()
        self.state = "UP"
        self.left_elbow_smoother.reset()
        self.right_elbow_smoother.reset()

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

        pushup_indices = [
            self.LEFT_SHOULDER, self.RIGHT_SHOULDER,
            self.LEFT_ELBOW, self.RIGHT_ELBOW,
            self.LEFT_WRIST, self.RIGHT_WRIST
        ]
        confidence = calculate_landmarks_average_confidence(landmarks, pushup_indices)

        if confidence < self.cfg.MIN_VISIBILITY:
            return ExerciseResult(
                exercise=self.name,
                reps=self.reps,
                state="LOW_CONFIDENCE",
                confidence=confidence,
                metrics={},
                feedback="Ensure upper body & arms are visible"
            )

        l_shoulder = get_landmark_coords(landmarks, self.LEFT_SHOULDER, w, h)[:2]
        l_elbow = get_landmark_coords(landmarks, self.LEFT_ELBOW, w, h)[:2]
        l_wrist = get_landmark_coords(landmarks, self.LEFT_WRIST, w, h)[:2]

        r_shoulder = get_landmark_coords(landmarks, self.RIGHT_SHOULDER, w, h)[:2]
        r_elbow = get_landmark_coords(landmarks, self.RIGHT_ELBOW, w, h)[:2]
        r_wrist = get_landmark_coords(landmarks, self.RIGHT_WRIST, w, h)[:2]

        raw_l_angle = calculate_angle_2d(l_shoulder, l_elbow, l_wrist)
        raw_r_angle = calculate_angle_2d(r_shoulder, r_elbow, r_wrist)

        smooth_l_angle = self.left_elbow_smoother.filter(raw_l_angle)
        smooth_r_angle = self.right_elbow_smoother.filter(raw_r_angle)

        avg_elbow_angle = (smooth_l_angle + smooth_r_angle) / 2.0

        if self.state == "UP" or self.state == "INITIALIZING":
            if avg_elbow_angle <= self.cfg.DOWN_THRESHOLD:
                self.state = "DOWN"
                self.feedback = "Chest down! Now push up!"
            else:
                self.feedback = "Lower chest toward ground"

        elif self.state == "DOWN":
            if avg_elbow_angle >= self.cfg.UP_THRESHOLD:
                self.reps += 1
                self.state = "UP"
                self.feedback = "Push-up completed! Great effort!"
            elif avg_elbow_angle > self.cfg.DOWN_THRESHOLD:
                self.feedback = "Lock out arms to complete rep"
            else:
                self.feedback = "Hold bottom position, then extend"

        return ExerciseResult(
            exercise=self.name,
            reps=self.reps,
            state=self.state,
            confidence=confidence,
            metrics={
                "elbow_angle": avg_elbow_angle,
                "left_elbow_angle": smooth_l_angle,
                "right_elbow_angle": smooth_r_angle
            },
            feedback=self.feedback
        )
