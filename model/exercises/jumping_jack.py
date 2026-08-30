"""
FitQuest Jumping Jack Recognition Module
Detects full-body landmarks (shoulders, wrists, hips, ankles), tracks arm elevation & leg spread, and manages state transitions.
"""

from typing import Any, List, Optional, Tuple

from backend.model.config import JUMPING_JACK_CFG
from backend.model.exercises.base import BaseExercise, ExerciseResult
from backend.model.utils import (
    EMASmoother,
    calculate_angle_2d,
    calculate_distance_2d,
    calculate_landmarks_average_confidence,
    get_landmark_coords,
)


class JumpingJackDetector(BaseExercise):
    """Jumping Jack exercise detector and rep counter."""

    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28

    def __init__(self, config=JUMPING_JACK_CFG):
        super().__init__(name="jumping_jack")
        self.cfg = config
        self.state = "CLOSED"
        self.reps = 0
        self.feedback = "Stand with feet together & arms at sides"

        self.arm_angle_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)
        self.feet_spread_smoother = EMASmoother(alpha=self.cfg.SMOOTHING_ALPHA)

    def reset(self):
        super().reset()
        self.state = "CLOSED"
        self.arm_angle_smoother.reset()
        self.feet_spread_smoother.reset()

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

        jj_indices = [
            self.LEFT_SHOULDER, self.RIGHT_SHOULDER,
            self.LEFT_WRIST, self.RIGHT_WRIST,
            self.LEFT_HIP, self.RIGHT_HIP,
            self.LEFT_ANKLE, self.RIGHT_ANKLE
        ]
        confidence = calculate_landmarks_average_confidence(landmarks, jj_indices)

        if confidence < self.cfg.MIN_VISIBILITY:
            return ExerciseResult(
                exercise=self.name,
                reps=self.reps,
                state="LOW_CONFIDENCE",
                confidence=confidence,
                metrics={},
                feedback="Step back so full body is visible"
            )

        l_shoulder = get_landmark_coords(landmarks, self.LEFT_SHOULDER, w, h)[:2]
        r_shoulder = get_landmark_coords(landmarks, self.RIGHT_SHOULDER, w, h)[:2]
        l_wrist = get_landmark_coords(landmarks, self.LEFT_WRIST, w, h)[:2]
        r_wrist = get_landmark_coords(landmarks, self.RIGHT_WRIST, w, h)[:2]
        l_hip = get_landmark_coords(landmarks, self.LEFT_HIP, w, h)[:2]
        r_hip = get_landmark_coords(landmarks, self.RIGHT_HIP, w, h)[:2]
        l_ankle = get_landmark_coords(landmarks, self.LEFT_ANKLE, w, h)[:2]
        r_ankle = get_landmark_coords(landmarks, self.RIGHT_ANKLE, w, h)[:2]

        raw_l_arm = calculate_angle_2d(l_wrist, l_shoulder, l_hip)
        raw_r_arm = calculate_angle_2d(r_wrist, r_shoulder, r_hip)
        avg_raw_arm = (raw_l_arm + raw_r_arm) / 2.0
        smooth_arm_angle = self.arm_angle_smoother.filter(avg_raw_arm)

        hip_dist = max(1.0, calculate_distance_2d(l_hip, r_hip))
        ankle_dist = calculate_distance_2d(l_ankle, r_ankle)
        raw_feet_ratio = ankle_dist / hip_dist
        smooth_feet_ratio = self.feet_spread_smoother.filter(raw_feet_ratio)

        is_arms_overhead = smooth_arm_angle >= self.cfg.HANDS_OVERHEAD_ANGLE
        is_feet_wide = smooth_feet_ratio >= self.cfg.FEET_SPREAD_RATIO_OPEN

        is_arms_down = smooth_arm_angle <= self.cfg.HANDS_DOWN_ANGLE
        is_feet_together = smooth_feet_ratio <= self.cfg.FEET_SPREAD_RATIO_CLOSED

        if self.state == "CLOSED" or self.state == "INITIALIZING":
            if is_arms_overhead and is_feet_wide:
                self.state = "OPEN"
                self.feedback = "Jumping jack open! Now jump back!"
            else:
                self.feedback = "Jump out: raise arms & spread feet"

        elif self.state == "OPEN":
            if is_arms_down and is_feet_together:
                self.reps += 1
                self.state = "CLOSED"
                self.feedback = "Jumping jack completed! Excellent!"
            elif is_arms_down or is_feet_together:
                self.feedback = "Return arms to sides & feet together"
            else:
                self.feedback = "Hold open position, then return"

        return ExerciseResult(
            exercise=self.name,
            reps=self.reps,
            state=self.state,
            confidence=confidence,
            metrics={
                "arm_angle": smooth_arm_angle,
                "feet_spread_ratio": smooth_feet_ratio
            },
            feedback=self.feedback
        )
