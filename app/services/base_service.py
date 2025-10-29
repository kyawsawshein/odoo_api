"""Base service class with common functionality"""

from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

# from sqlalchemy import select, and_, or_
import asyncio
import structlog

from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.odoo.client import OdooClientPool
from app.cache.redis_client import redis_client


logger = structlog.get_logger()


class BaseService:
    """Base service class with common functionality"""

    def __init__(self, db: AsyncSession, current_user: UserSchema):
        self.db = db
        self.current_user = current_user
        self.odoo_pool = OdooClientPool()
        self.logger = logger.bind(
            service=self.__class__.__name__, user_id=current_user.id
        )

    async def _get_odoo_client(self) -> OdooClientPool:
        """Get Odoo client from pool"""
        # In a real implementation, you would get Odoo credentials from user session
        return await self.odoo_pool.get_client(
            db="odoo",  # This should come from user configuration
            username="admin",  # This should come from user configuration
            password="admin",  # This should come from user configuration
        )

    async def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            return await redis_client.get(key)
        except Exception as e:
            self.logger.warning("Cache get failed", key=key, error=str(e))
            return None

    async def _cache_set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache"""
        try:
            await redis_client.set(key, value, expire=expire)
            return True
        except Exception as e:
            self.logger.warning("Cache set failed", key=key, error=str(e))
            return False

    async def _cache_delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            await redis_client.delete(key)
            return True
        except Exception as e:
            self.logger.warning("Cache delete failed", key=key, error=str(e))
            return False

    def _create_sync_response(
        self,
        success: bool,
        message: str,
        odoo_id: Optional[int] = None,
        local_id: Optional[int] = None,
        errors: List[str] = None,
    ) -> SyncResponse:
        """Create standardized sync response"""
        if errors is None:
            errors = []

        return SyncResponse(
            success=success,
            message=message,
            odoo_id=odoo_id,
            local_id=local_id,
            errors=errors,
        )

    async def _execute_with_retry(self, func, max_retries: int = 3, delay: float = 1.0):
        """Execute function with retry logic"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                self.logger.warning(
                    "Operation failed, retrying", attempt=attempt + 1, error=str(e)
                )
                await asyncio.sleep(delay * (attempt + 1))

    async def _handle_odoo_error(
        self, error: Exception, operation: str
    ) -> SyncResponse:
        """Handle Odoo operation errors"""
        error_msg = f"Odoo {operation} failed: {str(error)}"
        self.logger.error(error_msg, error=str(error))
        return self._create_sync_response(False, error_msg, errors=[str(error)])
