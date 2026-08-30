"""
FitQuest Pose Estimator Component
Encapsulates MediaPipe Pose estimation, processing webcam frames, and returning normalized landmark vectors.
"""

from typing import List, Optional, Tuple, Any
import cv2
import mediapipe as mp
import numpy as np

from backend.model.config import VISUALIZER_CFG


# Resolve MediaPipe solutions package across versions
try:
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
    else:
        import mediapipe.python.solutions.pose as mp_pose
        import mediapipe.python.solutions.drawing_utils as mp_drawing
        import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
except (AttributeError, ModuleNotFoundError) as err:
    raise RuntimeError(
        "MediaPipe Pose solution API is not available in the current mediapipe package.\n"
        "Please install the compatible package using:\n"
        "    pip install mediapipe==0.10.14\n"
    ) from err


class PoseEstimator:
    """Wrapper class around MediaPipe Pose estimation solution."""

    def __init__(
        self,
        static_image_mode: bool = False,
        model_complexity: int = 1,
        smooth_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """Initialize MediaPipe Pose instance."""
        self.mp_pose = mp_pose
        self.mp_drawing = mp_drawing
        self.mp_drawing_styles = mp_drawing_styles

        self.pose = self.mp_pose.Pose(
            static_image_mode=static_image_mode,
            model_complexity=model_complexity,
            smooth_landmarks=smooth_landmarks,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[List[Any]], Optional[Any]]:
        """
        Process a BGR webcam frame and return detected pose landmarks.
        
        :param frame: BGR image numpy array from OpenCV.
        :return: Tuple of (list of normalized landmarks, full MediaPipe raw results object).
        """
        if frame is None or frame.size == 0:
            return None, None

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb.flags.writeable = False

        results = self.pose.process(frame_rgb)

        landmarks = None
        if results and results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

        return landmarks, results

    def draw_skeleton(self, frame: np.ndarray, results: Any) -> np.ndarray:
        """
        Draw body landmark points and skeleton connection lines on an OpenCV frame.
        """
        if results is None or not getattr(results, 'pose_landmarks', None):
            return frame

        landmark_style = self.mp_drawing.DrawingSpec(
            color=VISUALIZER_CFG.COLOR_LANDMARK,
            thickness=3,
            circle_radius=4
        )
        connection_style = self.mp_drawing.DrawingSpec(
            color=VISUALIZER_CFG.COLOR_CONNECTION,
            thickness=2,
            circle_radius=2
        )

        self.mp_drawing.draw_landmarks(
            image=frame,
            landmark_list=results.pose_landmarks,
            connections=self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=landmark_style,
            connection_drawing_spec=connection_style
        )

        return frame

    def close(self):
        """Release MediaPipe resources."""
        if hasattr(self, 'pose') and self.pose is not None:
            self.pose.close()
