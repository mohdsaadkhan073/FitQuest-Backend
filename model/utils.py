"""
FitQuest Utility Module
Helper functions for joint angle calculations, landmark conversions, distance metrics, and time-series angle smoothing.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class EMASmoother:
    """Exponential Moving Average (EMA) filter for smoothing joint angle time-series."""

    def __init__(self, alpha: float = 0.3):
        """
        :param alpha: Smoothing factor between 0.0 (max smoothing/delay) and 1.0 (no smoothing).
        """
        self.alpha = max(0.01, min(1.0, alpha))
        self.current_value: Optional[float] = None

    def filter(self, value: float) -> float:
        if self.current_value is None:
            self.current_value = value
        else:
            self.current_value = self.alpha * value + (1.0 - self.alpha) * self.current_value
        return self.current_value

    def reset(self):
        self.current_value = None


def calculate_angle_2d(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float]
) -> float:
    """
    Calculate interior angle at point p2 formed by vectors (p1 -> p2) and (p3 -> p2).
    
    :param p1: (x, y) coordinates of first landmark
    :param p2: (x, y) coordinates of vertex landmark
    :param p3: (x, y) coordinates of third landmark
    :return: Angle in degrees in range [0, 180].
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    v1 = np.array([x1 - x2, y1 - y2])
    v2 = np.array([x3 - x2, y3 - y2])

    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    if norm_v1 < 1e-6 or norm_v2 < 1e-6:
        return 0.0

    cosine_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
    cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosine_angle))

    return float(angle)


def calculate_distance_2d(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two 2D points."""
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_landmark_coords(
    landmarks: List[Any],
    landmark_idx: int,
    image_width: int,
    image_height: int
) -> Tuple[float, float, float]:
    """
    Extract (pixel_x, pixel_y, visibility) for a specific landmark index.
    """
    if landmark_idx >= len(landmarks):
        return (0.0, 0.0, 0.0)

    lm = landmarks[landmark_idx]
    x_px = lm.x * image_width
    y_px = lm.y * image_height
    visibility = getattr(lm, 'visibility', 1.0)

    return (x_px, y_px, visibility)


def check_landmarks_visible(
    landmarks: List[Any],
    indices: List[int],
    min_visibility: float = 0.5
) -> bool:
    """Check if all specified landmark indices meet minimum visibility threshold."""
    if not landmarks:
        return False

    for idx in indices:
        if idx >= len(landmarks):
            return False
        if getattr(landmarks[idx], 'visibility', 1.0) < min_visibility:
            return False

    return True


def calculate_landmarks_average_confidence(
    landmarks: List[Any],
    indices: List[int]
) -> float:
    """Calculate average visibility score for landmark indices."""
    if not landmarks or not indices:
        return 0.0

    total_vis = 0.0
    count = 0
    for idx in indices:
        if idx < len(landmarks):
            total_vis += getattr(landmarks[idx], 'visibility', 1.0)
            count += 1

    return (total_vis / count) if count > 0 else 0.0
