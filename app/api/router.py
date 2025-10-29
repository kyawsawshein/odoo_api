"""Main API router for Odoo FastAPI integration"""

# from typing import List, Optional

import structlog
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema

from app.cache.redis_client import redis_client
# from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter()


# Cache Management
@router.delete("/cache", tags=["cache"])
async def clear_cache(current_user: UserSchema = Depends(get_current_user)):
    """Clear application cache"""
    try:
        await redis_client.flush_all()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )
