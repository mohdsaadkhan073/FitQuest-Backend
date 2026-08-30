"""
FitQuest Visualizer Component
Renders real-time HUD (Heads-Up Display) graphical overlays on OpenCV video frames.
"""

from typing import Any, Tuple
import cv2
import numpy as np

from backend.model.config import VISUALIZER_CFG
from backend.model.exercises.base import ExerciseResult


class Visualizer:
    """Renders FitQuest UI overlay on top of webcam feed."""

    def __init__(self, config=VISUALIZER_CFG):
        self.cfg = config

    def draw_hud(
        self,
        frame: np.ndarray,
        result: ExerciseResult,
        fps: float = 0.0
    ) -> np.ndarray:
        """
        Draw FitQuest HUD panel onto video frame.
        
        :param frame: BGR image frame from OpenCV.
        :param result: ExerciseResult output object.
        :param fps: Frames per second float.
        :return: Frame with HUD overlay.
        """
        h, w, _ = frame.shape

        # 1. Top Header Banner
        header_height = 60
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, header_height), self.cfg.COLOR_BG_HUD, -1)

        # 2. Main Left Data Panel (Expanded width to fit long states cleanly)
        panel_w = 380
        panel_h = 320
        cv2.rectangle(overlay, (20, 80), (20 + panel_w, 80 + panel_h), self.cfg.COLOR_BG_HUD, -1)

        # 3. Bottom Hotkey Bar Panel
        cv2.rectangle(overlay, (0, h - 45), (w, h), self.cfg.COLOR_BG_HUD, -1)

        # Blend semi-transparent background cards (alpha = 0.75)
        alpha = 0.75
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

        # Draw Header Text
        cv2.putText(
            frame, "FITQUEST  |  CV RECOGNITION SYSTEM",
            (25, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.85, self.cfg.COLOR_PRIMARY, 2, cv2.LINE_AA
        )

        if fps > 0:
            fps_str = f"FPS: {fps:.1f}"
            cv2.putText(
                frame, fps_str,
                (w - 140, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, self.cfg.COLOR_TEXT_DIM, 2, cv2.LINE_AA
            )

        # --- PANEL CONTENT ---
        x0 = 35
        y0 = 115

        # Active Exercise Label
        cv2.putText(
            frame, "EXERCISE",
            (x0, y0), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.cfg.COLOR_TEXT_DIM, 1, cv2.LINE_AA
        )
        exercise_display_name = result.exercise.upper().replace("_", " ")
        cv2.putText(
            frame, exercise_display_name,
            (x0, y0 + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.95, self.cfg.COLOR_TEXT, 2, cv2.LINE_AA
        )

        # Repetition Count Display
        cv2.putText(
            frame, "REPETITIONS",
            (x0, y0 + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.cfg.COLOR_TEXT_DIM, 1, cv2.LINE_AA
        )
        cv2.putText(
            frame, str(result.reps),
            (x0, y0 + 135), cv2.FONT_HERSHEY_SIMPLEX, 1.8, self.cfg.COLOR_ACCENT, 3, cv2.LINE_AA
        )

        # Exercise State Indicator (with dynamic font scaling to prevent HUD card overflow)
        cv2.putText(
            frame, "STATE",
            (x0 + 160, y0 + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.cfg.COLOR_TEXT_DIM, 1, cv2.LINE_AA
        )
        
        state_str = str(result.state)
        state_color = self.cfg.COLOR_PRIMARY
        if state_str in ["DOWN", "OPEN"]:
            state_color = self.cfg.COLOR_SECONDARY
        elif state_str in ["UP", "CLOSED"]:
            state_color = self.cfg.COLOR_ACCENT

        # Dynamically scale font size according to string length (e.g. LOW_CONFIDENCE, INITIALIZING)
        if len(state_str) <= 6:
            state_font_scale = 0.85
            state_y_offset = 120
        elif len(state_str) <= 10:
            state_font_scale = 0.65
            state_y_offset = 118
        else:
            # For longer text like "LOW_CONFIDENCE" or "INITIALIZING"
            state_font_scale = 0.48
            state_y_offset = 115

        cv2.putText(
            frame, state_str,
            (x0 + 160, y0 + state_y_offset), cv2.FONT_HERSHEY_SIMPLEX, state_font_scale, state_color, 2, cv2.LINE_AA
        )

        # Primary Metric Angle / Distance Value
        if result.metrics:
            first_metric_key = list(result.metrics.keys())[0]
            val = result.metrics[first_metric_key]
            metric_str = f"{first_metric_key}: {val:.1f}"
            cv2.putText(
                frame, metric_str,
                (x0, y0 + 175), cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.cfg.COLOR_TEXT, 1, cv2.LINE_AA
            )

        # Confidence Meter Bar
        cv2.putText(
            frame, f"CONFIDENCE: {int(result.confidence * 100)}%",
            (x0, y0 + 210), cv2.FONT_HERSHEY_SIMPLEX, 0.45, self.cfg.COLOR_TEXT_DIM, 1, cv2.LINE_AA
        )
        bar_x = x0
        bar_y = y0 + 220
        bar_w = 310
        bar_h = 8
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
        fill_w = int(bar_w * max(0.0, min(1.0, result.confidence)))
        conf_color = self.cfg.COLOR_ACCENT if result.confidence >= 0.5 else self.cfg.COLOR_SECONDARY
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), conf_color, -1)

        # Real-time Form Feedback Banner
        if result.feedback:
            cv2.putText(
                frame, f"FEEDBACK: {result.feedback}",
                (x0, y0 + 265), cv2.FONT_HERSHEY_SIMPLEX, 0.48, self.cfg.COLOR_PRIMARY, 1, cv2.LINE_AA
            )

        # --- BOTTOM HOTKEY GUIDES BAR ---
        controls_text = "[1] Squat   [2] Push-up   [3] Jumping Jack   [R] Reset   [Q] Quit"
        cv2.putText(
            frame, controls_text,
            (25, h - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.cfg.COLOR_TEXT, 1, cv2.LINE_AA
        )

        return frame
