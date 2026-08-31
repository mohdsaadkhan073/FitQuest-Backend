"""
FitQuest Camera Stream Service (Non-Blocking Hardware Kill & 1-Second Reset Pipeline)
"""

import gc
import threading
import time
from typing import Generator, Optional
import cv2

from backend.model.config import VISUALIZER_CFG
from backend.model.exercise_manager import ExerciseManager
from backend.model.pose_estimator import PoseEstimator
from backend.model.visualizer import Visualizer
from backend.src.services.session_service import shared_session_service as session_service


class CameraStreamService:
    """
    Robust singleton service managing camera hardware capture, pose estimation inference,
    complete model termination, and non-blocking 1-second clean reboot cycle.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.pose_estimator: Optional[PoseEstimator] = None
        self.exercise_manager: Optional[ExerciseManager] = None
        self.visualizer: Optional[Visualizer] = None

        self._lock = threading.Lock()
        self._frame_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._active_session_id: Optional[str] = None
        
        # Pre-populate with placeholder frame
        placeholder = self._create_placeholder_frame("Connecting to webcam...")
        _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 70])
        self._latest_jpeg: Optional[bytes] = jpeg.tobytes()

    def _open_camera(self) -> Optional[cv2.VideoCapture]:
        """Attempt to open camera across DirectShow and default backends."""
        for backend in [cv2.CAP_DSHOW, cv2.CAP_ANY]:
            for idx in [self.camera_index, 0, 1]:
                try:
                    cap = cv2.VideoCapture(idx, backend) if backend != cv2.CAP_ANY else cv2.VideoCapture(idx)
                    if cap and cap.isOpened():
                        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        return cap
                except Exception:
                    continue
        return None

    def _initialize_hardware(self):
        """Initialize fresh MediaPipe models and open camera."""
        if self.pose_estimator is None:
            self.pose_estimator = PoseEstimator(model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        if self.exercise_manager is None:
            self.exercise_manager = ExerciseManager()
        if self.visualizer is None:
            self.visualizer = Visualizer()

        if self.cap is None or not self.cap.isOpened():
            self.cap = self._open_camera()

    def start(self, session_id: Optional[str] = None):
        """Start the background camera and inference worker thread."""
        with self._lock:
            if session_id:
                self._active_session_id = session_id

            if self._is_running and self._worker_thread and self._worker_thread.is_alive():
                return

            self._is_running = True
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

    def stop(self):
        """Completely kill model, release camera hardware, and force memory garbage collection."""
        with self._lock:
            self._is_running = False
            self._frame_event.set()

        # Release OpenCV Camera
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        # Kill MediaPipe Pose Estimator
        if self.pose_estimator is not None:
            try:
                self.pose_estimator.close()
            except Exception:
                pass
            self.pose_estimator = None

        self.exercise_manager = None
        self.visualizer = None

        placeholder = self._create_placeholder_frame("Camera resetting...")
        _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 70])
        self._latest_jpeg = jpeg.tobytes()
        self._frame_event.set()

        gc.collect()

    def restart(self, session_id: Optional[str] = None):
        """
        Non-blocking restart: Spawns a background thread to kill the model,
        wait 1.0 second for OS driver release, and start fresh without blocking HTTP response.
        """
        def _do_restart():
            try:
                self.stop()
                time.sleep(1.0)
                self.start(session_id=session_id)
            except Exception as e:
                print(f"[CameraStreamService] Restart error: {e}")

        # Run reboot in thread so HTTP endpoint responds immediately
        reboot_thread = threading.Thread(target=_do_restart, daemon=True)
        reboot_thread.start()
        return {"status": "restarting", "active": True}

    def set_active_exercise(self, exercise_name: str) -> bool:
        """Switch active exercise target in model."""
        if self.exercise_manager:
            return self.exercise_manager.set_active_exercise(exercise_name)
        return False

    def is_active(self) -> bool:
        """Return True if worker is actively running."""
        return self._is_running and self.cap is not None and self.cap.isOpened()

    def _worker_loop(self):
        """Dedicated background loop capturing newest frames and running inference."""
        self._initialize_hardware()
        prev_time = time.time()
        fail_count = 0

        while self._is_running:
            if self.cap is None or not self.cap.isOpened():
                self._initialize_hardware()
                if self.cap is None or not self.cap.isOpened():
                    placeholder = self._create_placeholder_frame("Webcam busy or not detected. Click Restart Camera.")
                    _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    self._latest_jpeg = jpeg.tobytes()
                    self._frame_event.set()
                    time.sleep(0.5)
                    continue

            ret, frame = self.cap.read()
            if not ret or frame is None:
                fail_count += 1
                if fail_count > 10:
                    if self.cap:
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                    self.cap = None
                    fail_count = 0
                time.sleep(0.02)
                continue

            fail_count = 0

            # Mirror frame horizontally for natural self-view
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Compute FPS
            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0.0
            prev_time = curr_time

            # 1. Pose Landmark Estimation
            landmarks, results = self.pose_estimator.process_frame(frame)

            # 2. Exercise State & Repetition Update
            exercise_result = self.exercise_manager.process_landmarks(
                landmarks=landmarks,
                image_shape=(h, w)
            )

            # 3. Synchronize with active backend WorkoutSession
            if self._active_session_id and exercise_result:
                active_sess = session_service.get_session(self._active_session_id)
                if active_sess and active_sess.current_exercise_target:
                    active_ex = active_sess.current_exercise_target.exercise
                    if self.exercise_manager.active_name != active_ex:
                        self.exercise_manager.set_active_exercise(active_ex)

                session_service.process_exercise_result(self._active_session_id, exercise_result)

            # 4. Draw Skeleton Overlay & FitQuest HUD
            frame = self.pose_estimator.draw_skeleton(frame, results)
            frame = self.visualizer.draw_hud(frame, exercise_result, fps=fps)

            # 5. Compress to fast JPEG
            ret_enc, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 68])
            if ret_enc:
                self._latest_jpeg = jpeg.tobytes()
                self._frame_event.set()

            time.sleep(0.01)

    def generate_mjpeg_stream(self, session_id: Optional[str] = None) -> Generator[bytes, None, None]:
        """
        Generate fast, smooth multipart MJPEG video stream chunks for web browser preview.
        """
        self.start(session_id=session_id)

        try:
            while self._is_running:
                self._frame_event.wait(timeout=0.3)
                self._frame_event.clear()
                if self._latest_jpeg:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + self._latest_jpeg + b'\r\n')
        except GeneratorExit:
            pass
        except Exception as e:
            print(f"[CameraStreamService] Client disconnected: {e}")

    def _create_placeholder_frame(self, message: str):
        """Create clean dark placeholder frame with message."""
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (20, 24, 35)
        cv2.putText(frame, "FITQUEST CAMERA", (180, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 140, 0), 2)
        cv2.putText(frame, message, (80, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        return frame


# Global singleton instance
camera_stream_service = CameraStreamService()
