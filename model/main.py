"""
FitQuest Model Main Entry Point
Runnable entry point for real-time computer-vision exercise recognition and repetition counting.

Usage:
    python backend/model/main.py [--camera CAMERA_INDEX]

Keyboard Controls:
    1 - Select Squats
    2 - Select Push-ups
    3 - Select Jumping Jacks
    r - Reset repetition count
    q - Quit application
"""

import argparse
import os
import sys
import time
import cv2

# Ensure project root directory is in sys.path when script is executed directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.model.config import KEY_CFG, VISUALIZER_CFG
from backend.model.exercise_manager import ExerciseManager
from backend.model.pose_estimator import PoseEstimator
from backend.model.visualizer import Visualizer


def run_fitquest_model(camera_index: int = 0):
    """
    Main loop initializing camera, pose estimator, exercise manager, and visualizer.
    
    :param camera_index: Webcam device index (default 0 for built-in laptop webcam).
    """
    print("=" * 60)
    print("           FITQUEST - COMPUTER VISION EXERCISE MODEL          ")
    print("=" * 60)
    print("Initializing MediaPipe Pose Estimator & Exercise Registry...")

    pose_estimator = PoseEstimator()
    exercise_manager = ExerciseManager()
    visualizer = Visualizer()

    print(f"Opening camera index {camera_index}...")
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"\n[ERROR] Could not open camera at index {camera_index}.")
        print("Please verify your laptop webcam is connected and not in use by another app.")
        print("Exiting FitQuest model cleanly.")
        pose_estimator.close()
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, VISUALIZER_CFG.WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VISUALIZER_CFG.WINDOW_HEIGHT)

    print("\nFitQuest model running successfully!")
    print("Controls:")
    print("  [1] - Switch to Squats")
    print("  [2] - Switch to Push-ups")
    print("  [3] - Switch to Jumping Jacks")
    print("  [r] - Reset rep count")
    print("  [q] - Quit")
    print("-" * 60)

    prev_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("\n[WARNING] Failed to capture frame from webcam. Retrying...")
                time.sleep(0.1)
                continue

            frame = cv2.flip(frame, 1)
            image_h, image_w, _ = frame.shape

            curr_time = time.time()
            fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0.0
            prev_time = curr_time

            landmarks, results = pose_estimator.process_frame(frame)

            exercise_result = exercise_manager.process_landmarks(
                landmarks=landmarks,
                image_shape=(image_h, image_w)
            )

            frame = pose_estimator.draw_skeleton(frame, results)
            frame = visualizer.draw_hud(frame, exercise_result, fps=fps)

            cv2.imshow(VISUALIZER_CFG.WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == KEY_CFG.KEY_QUIT or key == KEY_CFG.KEY_ESC:
                print("\nQuit command received. Closing FitQuest...")
                break
            elif key == KEY_CFG.KEY_SQUAT:
                if exercise_manager.set_active_exercise("squat"):
                    print("[KEYPRESS] Switched active exercise to: SQUATS")
            elif key == KEY_CFG.KEY_PUSHUP:
                if exercise_manager.set_active_exercise("pushup"):
                    print("[KEYPRESS] Switched active exercise to: PUSH-UPS")
            elif key == KEY_CFG.KEY_JUMPING_JACK:
                if exercise_manager.set_active_exercise("jumping_jack"):
                    print("[KEYPRESS] Switched active exercise to: JUMPING JACKS")
            elif key == KEY_CFG.KEY_RESET:
                exercise_manager.reset_current_reps()
                print(f"[KEYPRESS] Reset repetition count for {exercise_manager.active_name.upper()}")

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pose_estimator.close()
        print("FitQuest resources released cleanly. Goodbye!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FitQuest Computer Vision Exercise Recognition")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index (default: 0)")
    args = parser.parse_args()

    run_fitquest_model(camera_index=args.camera)
