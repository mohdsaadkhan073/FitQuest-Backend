"""
FitQuest FastAPI Application Entry Point
Exposes REST API endpoints for workout management, session progression, model integration, and scoring.
"""

import os
import sys
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Ensure project root is in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.src.routes.session_routes import router as session_router
from backend.src.routes.workout_routes import router as workout_router
from backend.src.schemas import HealthCheckSchema

app = FastAPI(
    title="FitQuest API",
    description="Interactive Computer-Vision Family Fitness & Reward System Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware enabling cross-origin calls from local web frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(workout_router)
app.include_router(session_router)


@app.get("/health", response_model=HealthCheckSchema, tags=["Health"])
def health_check():
    """Health check status endpoint."""
    return HealthCheckSchema(status="ok", service="FitQuest Backend API", version="1.0.0")


@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    """Global exception handler converting domain ValueError to HTTP 400 Bad Request."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )
