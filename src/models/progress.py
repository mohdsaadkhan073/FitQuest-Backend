"""
FitQuest Set Progress Domain Model
Represents real-time progress for an individual exercise set (e.g. Set 1: 15/20 reps).
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SetProgress:
    """Tracks progress for a single set within an exercise."""
    set_number: int            # 1-indexed set number
    target_reps: int           # Target reps required to complete this set
    completed_reps: int = 0    # Valid reps completed so far in this set

    def __post_init__(self):
        if self.set_number <= 0:
            raise ValueError(f"Set number must be positive, got {self.set_number}")
        if self.target_reps <= 0:
            raise ValueError(f"Target reps must be positive, got {self.target_reps}")
        if self.completed_reps < 0:
            self.completed_reps = 0

    @property
    def is_complete(self) -> bool:
        """True if completed reps have met or exceeded target reps."""
        return self.completed_reps >= self.target_reps

    @property
    def remaining_reps(self) -> int:
        """Number of reps remaining to complete this set."""
        return max(0, self.target_reps - self.completed_reps)

    def add_reps(self, count: int) -> int:
        """
        Add valid reps to set.
        :param count: Rep count increment.
        :return: Actual reps accepted toward this set.
        """
        if count <= 0 or self.is_complete:
            return 0

        needed = self.remaining_reps
        accepted = min(count, needed)
        self.completed_reps += accepted
        return accepted

    def to_dict(self) -> Dict[str, Any]:
        """Serialize SetProgress to standard dictionary."""
        return {
            "set_number": self.set_number,
            "target_reps": self.target_reps,
            "completed_reps": self.completed_reps,
            "remaining_reps": self.remaining_reps,
            "is_complete": self.is_complete
        }
