"""
FitQuest Scoring Service
Calculates points for completed repetitions based on configured exercise rates and evaluates target point achievements.
"""

from typing import Dict
from backend.src.models.exercise_target import ExerciseTarget


class ScoringService:
    """Configurable scoring engine for calculating points and evaluating target scores."""

    @staticmethod
    def calculate_rep_points(target: ExerciseTarget, valid_reps: int) -> int:
        """
        Calculate points earned for a given number of valid reps.
        
        :param target: ExerciseTarget containing points_per_rep.
        :param valid_reps: Number of valid completed reps.
        :return: Total points earned (integer).
        """
        if valid_reps <= 0:
            return 0
        return valid_reps * target.points_per_rep

    @staticmethod
    def is_target_reached(current_points: int, target_points: int) -> bool:
        """
        Evaluate if current points meet or exceed target points.
        Uses current_points >= target_points.
        """
        return current_points >= target_points
