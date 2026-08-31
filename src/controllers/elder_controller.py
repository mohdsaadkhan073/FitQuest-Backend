"""
FitQuest Elder Profile Controller
Handles business logic for fetching/updating elder profile, persistent points state, and manual points resets.
"""

from fastapi import HTTPException, status
from backend.src.db.elder_repo import elder_repo
from backend.src.schemas import (
    ElderProfileSchema,
    UpdateElderProfileSchema,
    ResetPointsResponseSchema,
)


class ElderController:
    """Controller delegating elder profile operations to ElderRepository."""

    @staticmethod
    def get_profile() -> ElderProfileSchema:
        """Retrieve current elder profile and evaluated points."""
        profile = elder_repo.get_profile()
        return ElderProfileSchema(**profile)

    @staticmethod
    def update_profile(payload: UpdateElderProfileSchema) -> ElderProfileSchema:
        """Update elder profile and reset schedule settings."""
        try:
            updated = elder_repo.update_profile(
                elder_name=payload.elder_name,
                age=payload.age,
                reset_schedule=payload.reset_schedule,
                target_points=payload.target_points,
            )
            return ElderProfileSchema(**updated)
        except Exception as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    @staticmethod
    def reset_points() -> ResetPointsResponseSchema:
        """Manually reset elder current points to 0."""
        profile = elder_repo.reset_points()
        return ResetPointsResponseSchema(
            status="reset",
            current_points=0,
            last_points_reset_at=profile["last_points_reset_at"],
            message="Elder points successfully reset to 0.",
        )


shared_elder_controller = ElderController()
