"""Main API router for Odoo FastAPI integration"""

# from typing import List, Optional

import structlog
from app.auth.api.v1 import get_current_user, validate_token
from app.auth.models.models import User

from app.cache.redis_client import redis_client
from fastapi import APIRouter, Depends, HTTPException, status

PREFIX = "/cache"
TAG_NAME = "Cache"

router = APIRouter(
    prefix=PREFIX,
    tags=[TAG_NAME],
    dependencies=[Depends(validate_token)]
)

logger = structlog.get_logger()


# Cache Management
@router.delete("/cache")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """Clear application cache"""
    try:
        await redis_client.flush_all()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )
