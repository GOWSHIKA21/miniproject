from fastapi import APIRouter
from backend.app.services.patent_service import patent_service

router = APIRouter(prefix="/stats", tags=["Statistics"])

@router.get("")
def get_system_stats():
    """Get aggregated patent counts, domain taxonomy breakdowns, and system metrics."""
    return patent_service.get_dataset_stats()
