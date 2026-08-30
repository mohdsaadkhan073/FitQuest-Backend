"""
FitQuest Model Configuration
Contains all thresholds, landmark indices, visual styling parameters, and hotkey configurations.
"""

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass
class SquatConfig:
    # Knee angle thresholds (degrees)
    UP_THRESHOLD: float = 158.0   # Angle above which user is considered standing (UP)
    DOWN_THRESHOLD: float = 140.0  # Angle below which user is considered in squat depth (DOWN) - Shallow bend
    MIN_VISIBILITY: float = 0.5   # Minimum landmark confidence score to process leg joints
    SMOOTHING_ALPHA: float = 0.6  # Exponential Moving Average factor (0-1) for angle smoothing


@dataclass
class PushUpConfig:
    # Elbow angle thresholds (degrees)
    UP_THRESHOLD: float = 150.0   # Arms extended
    DOWN_THRESHOLD: float = 110.0  # Arms bent at bottom of push-up
    # Body posture alignment: shoulder-hip-ankle line angle max deviation from straight line
    BODY_ALIGNMENT_MAX_ANGLE: float = 40.0 
    MIN_VISIBILITY: float = 0.5
    SMOOTHING_ALPHA: float = 0.4


@dataclass
class JumpingJackConfig:
    # Arm angle threshold (degrees between torso-shoulder-wrist vector and vertical)
    HANDS_OVERHEAD_ANGLE: float = 140.0  # Arms raised overhead (OPEN)
    HANDS_DOWN_ANGLE: float = 40.0       # Arms at sides (CLOSED)
    # Leg spread ratio: (ankle distance / hip distance)
    FEET_SPREAD_RATIO_OPEN: float = 1.6  # Feet spread apart in OPEN state
    FEET_SPREAD_RATIO_CLOSED: float = 1.15  # Feet close together in CLOSED state
    MIN_VISIBILITY: float = 0.5
    SMOOTHING_ALPHA: float = 0.3


@dataclass
class VisualizerConfig:
    # Window settings
    WINDOW_NAME: str = "FitQuest - Exercise Recognition & Rep Counter"
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 720
    
    # Color palette (BGR format for OpenCV)
    COLOR_PRIMARY: Tuple[int, int, int] = (255, 140, 0)      # Deep Neon Orange / Cyan accent
    COLOR_ACCENT: Tuple[int, int, int] = (0, 230, 115)       # Mint Green (for completed reps / UP state)
    COLOR_SECONDARY: Tuple[int, int, int] = (0, 75, 255)     # Coral Red (for DOWN state / warnings)
    COLOR_BG_HUD: Tuple[int, int, int] = (20, 20, 30)        # Dark Charcoal HUD overlay
    COLOR_TEXT: Tuple[int, int, int] = (255, 255, 255)       # White
    COLOR_TEXT_DIM: Tuple[int, int, int] = (180, 180, 180)   # Light Gray
    COLOR_LANDMARK: Tuple[int, int, int] = (0, 255, 255)    # Yellow joint nodes
    COLOR_CONNECTION: Tuple[int, int, int] = (255, 128, 0)  # Bright connection lines


@dataclass
class KeyConfig:
    KEY_SQUAT: int = ord('1')
    KEY_PUSHUP: int = ord('2')
    KEY_JUMPING_JACK: int = ord('3')
    KEY_RESET: int = ord('r')
    KEY_QUIT: int = ord('q')
    KEY_ESC: int = 27  # ESC key code


# Instantiated global configuration defaults
SQUAT_CFG = SquatConfig()
PUSHUP_CFG = PushUpConfig()
JUMPING_JACK_CFG = JumpingJackConfig()
VISUALIZER_CFG = VisualizerConfig()
KEY_CFG = KeyConfig()
