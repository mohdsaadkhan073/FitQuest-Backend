"""
FitQuest Camera Stream API Routes
FastAPI APIRouter for live video streaming, model preview, and camera hardware control.
"""

from typing import Optional
from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse

from backend.src.services.camera_stream_service import camera_stream_service

router = APIRouter(prefix="/api/v1/stream", tags=["Camera Stream"])


@router.get("/video_feed")
def video_feed(session_id: Optional[str] = Query(None, description="Active workout session ID to sync")):
    """
    Stream live camera video with pose estimation skeleton and exercise HUD overlay.
    Returns standard multipart MJPEG stream for embedding in HTML <img> tags.
    """
    return StreamingResponse(
        camera_stream_service.generate_mjpeg_stream(session_id=session_id),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/start", status_code=status.HTTP_200_OK)
def start_camera(session_id: Optional[str] = None):
    """Start camera hardware capture."""
    camera_stream_service.start(session_id=session_id)
    return {"status": "started", "active": camera_stream_service.is_active()}


@router.post("/stop", status_code=status.HTTP_200_OK)
def stop_camera():
    """Stop camera hardware capture and release device."""
    camera_stream_service.stop()
    return {"status": "stopped", "active": False}


@router.post("/restart", status_code=status.HTTP_200_OK)
def restart_camera(session_id: Optional[str] = None):
    """Perform a full hard reset of camera hardware and restart streaming."""
    return camera_stream_service.restart(session_id=session_id)


@router.get("/status")
def get_stream_status():
    """Check if camera stream is active."""
    return {"active": camera_stream_service.is_active()}
