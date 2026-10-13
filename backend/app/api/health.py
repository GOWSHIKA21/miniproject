from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter(tags=["Health"])

@router.get("/health")
def get_health_status():
    """Health check endpoint to verify backend service readiness."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }
