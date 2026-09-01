"""
FitQuest Camera Stream Service (Ultra-Fast 30-60 FPS Non-Blocking Pipeline)
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
from backend.src.services.session_service import shared_session_service as session_service, normalize_ex_name


class CameraStreamService:
    """
    Robust singleton service managing camera capture, pose estimation inference,
    multi-client lock-free streaming, and non-blocking 1-second reset pipeline.
    """

    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.pose_estimator: Optional[PoseEstimator] = None
        self.exercise_manager: Optional[ExerciseManager] = None
        self.visualizer: Optional[Visualizer] = None

        self._lock = threading.Lock()
        self._worker_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._active_session_id: Optional[str] = None
        self._frame_id: int = 0
        
        # Pre-populate with placeholder frame
        placeholder = self._create_placeholder_frame("Connecting to webcam...")
        _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 60])
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
                        cap.set(cv2.CAP_PROP_FPS, 30)
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
            if session_id and not session_id.startswith('session-') and session_id != 'null':
                self._active_session_id = session_id

            if self._is_running and self._worker_thread and self._worker_thread.is_alive():
                return

            self._is_running = True
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

    def stop(self):
        """Completely release camera hardware, kill models, and collect memory."""
        with self._lock:
            self._is_running = False

        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

        if self.pose_estimator is not None:
            try:
                self.pose_estimator.close()
            except Exception:
                pass
            self.pose_estimator = None

        self.exercise_manager = None
        self.visualizer = None

        placeholder = self._create_placeholder_frame("Camera resetting...")
        _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 60])
        self._latest_jpeg = jpeg.tobytes()
        self._frame_id += 1

        gc.collect()

    def restart(self, session_id: Optional[str] = None):
        """
        Non-blocking restart in dedicated thread.
        """
        def _do_restart():
            try:
                self.stop()
                time.sleep(0.8)
                self.start(session_id=session_id)
            except Exception as e:
                print(f"[CameraStreamService] Restart error: {e}")

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
        """Dedicated high-speed background loop capturing frames and running realtime inference."""
        self._initialize_hardware()
        prev_time = time.time()
        fail_count = 0

        while self._is_running:
            if self.cap is None or not self.cap.isOpened():
                self._initialize_hardware()
                if self.cap is None or not self.cap.isOpened():
                    placeholder = self._create_placeholder_frame("Webcam busy or not detected. Click Restart Camera.")
                    _, jpeg = cv2.imencode('.jpg', placeholder, [cv2.IMWRITE_JPEG_QUALITY, 60])
                    self._latest_jpeg = jpeg.tobytes()
                    self._frame_id += 1
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
                time.sleep(0.01)
                continue

            fail_count = 0

            # Mirror frame horizontally for natural self-view
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Compute real FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            fps = 1.0 / dt if dt > 0 else 30.0
            prev_time = curr_time

            # 1. Pose Landmark Estimation (fast complexity=0)
            landmarks, results = self.pose_estimator.process_frame(frame)

            # 2. Exercise State & Repetition Update
            exercise_result = self.exercise_manager.process_landmarks(
                landmarks=landmarks,
                image_shape=(h, w)
            )

            # 3. Synchronize with active backend WorkoutSession (in-memory 0ms)
            if exercise_result:
                active_sess = None
                if self._active_session_id and not self._active_session_id.startswith('session-'):
                    active_sess = session_service.get_session(self._active_session_id)

                if not active_sess or active_sess.is_completed:
                    all_sessions = [s for s in session_service.list_sessions() if not s.is_completed]
                    if all_sessions:
                        active_sess = all_sessions[-1]
                        self._active_session_id = active_sess.session_id

                if active_sess and not active_sess.is_completed:
                    if active_sess.current_exercise_target:
                        active_ex = normalize_ex_name(active_sess.current_exercise_target.exercise)
                        if self.exercise_manager.active_name != active_ex:
                            self.exercise_manager.set_active_exercise(active_ex)

                    session_service.process_exercise_result(active_sess.session_id, exercise_result)

            # 4. Draw Skeleton Overlay & FitQuest HUD
            frame = self.pose_estimator.draw_skeleton(frame, results)
            frame = self.visualizer.draw_hud(frame, exercise_result, fps=fps)

            # 5. Compress to fast JPEG
            ret_enc, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            if ret_enc:
                self._latest_jpeg = jpeg.tobytes()
                self._frame_id += 1

    def generate_mjpeg_stream(self, session_id: Optional[str] = None) -> Generator[bytes, None, None]:
        """
        Generate lock-free multipart MJPEG video stream chunks for web browser preview.
        Multiple clients receive full frame rate without thread starving or lock contention.
        """
        self.start(session_id=session_id)
        last_sent_frame_id = -1

        try:
            while self._is_running:
                if self._latest_jpeg is not None and self._frame_id != last_sent_frame_id:
                    last_sent_frame_id = self._frame_id
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + self._latest_jpeg + b'\r\n')
                time.sleep(0.012)
        except GeneratorExit:
            pass
        except Exception as e:
            print(f"[CameraStreamService] Stream client disconnected: {e}")

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
