"""API endpoint to check storage configuration."""
from fastapi import APIRouter, Depends
from app.auth.jwt import get_current_user
from app.storage.artifacts import get_storage_info

router = APIRouter(prefix="/api/storage", tags=["storage"])


@router.get("/info")
async def storage_info(current_user: dict = Depends(get_current_user)):
    """
    Get current storage backend configuration.
    
    Returns info about local disk vs S3 usage.
    """
    info = get_storage_info()
    return {
        "status": "ok",
        "storage": info
    }

