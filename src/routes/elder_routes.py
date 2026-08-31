"""
FitQuest Elder API Routes
FastAPI APIRouter for /api/v1/elder endpoints.
"""

from fastapi import APIRouter, status
from backend.src.controllers.elder_controller import ElderController
from backend.src.schemas import (
    ElderProfileSchema,
    UpdateElderProfileSchema,
    ResetPointsResponseSchema,
    OverrideLockSchema,
)

router = APIRouter(prefix="/api/v1/elder", tags=["Elder"])


@router.get("/profile", response_model=ElderProfileSchema)
def get_elder_profile():
    """Retrieve active elder profile, current points, and reset schedule."""
    return ElderController.get_profile()


@router.put("/profile", response_model=ElderProfileSchema)
def update_elder_profile(payload: UpdateElderProfileSchema):
    """Update elder profile settings (name, age, reset schedule, target points)."""
    return ElderController.update_profile(payload)


@router.post("/reset-points", response_model=ResetPointsResponseSchema)
def reset_elder_points():
    """Manually reset elder accumulated points to 0."""
    return ElderController.reset_points()


@router.post("/override-lock", response_model=ElderProfileSchema)
def override_elder_lock(payload: OverrideLockSchema):
    """Manually lock or unlock the physical reward box."""
    return ElderController.override_lock(payload)
