"""Redis client for caching and session management"""

import json
from typing import Any, Optional
import redis.asyncio as redis
import structlog

from app.config import settings


logger = structlog.get_logger()


class RedisClient:
    """Redis client wrapper with async operations"""

    _instance = None

    def __init__(self):
        if RedisClient._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            self.client = None
            self._connect()
            RedisClient._instance = self

    def _connect(self):
        """Connect to Redis server"""
        try:
            self.client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
            logger.info("Redis client connected successfully")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise

    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = RedisClient()
        return cls._instance

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = await self.client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.warning("Redis get failed", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in Redis with expiration"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            await self.client.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.warning("Redis set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            result = await self.client.delete(key)
            return result > 0
        except Exception as e:
            logger.warning("Redis delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            result = await self.client.exists(key)
            return result > 0
        except Exception as e:
            logger.warning("Redis exists failed", key=key, error=str(e))
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            result = await self.client.expire(key, seconds)
            return result
        except Exception as e:
            logger.warning("Redis expire failed", key=key, error=str(e))
            return False

    async def flush_all(self) -> bool:
        """Clear all Redis data"""
        try:
            await self.client.flushall()
            logger.info("Redis cache cleared")
            return True
        except Exception as e:
            logger.error("Redis flush failed", error=str(e))
            return False

    async def get_keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern"""
        try:
            return await self.client.keys(pattern)
        except Exception as e:
            logger.warning("Redis keys failed", pattern=pattern, error=str(e))
            return []

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter value"""
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.warning("Redis increment failed", key=key, error=str(e))
            return None

    async def set_hash(self, key: str, field: str, value: Any) -> bool:
        """Set hash field value"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            await self.client.hset(key, field, value)
            return True
        except Exception as e:
            logger.warning("Redis hset failed", key=key, field=field, error=str(e))
            return False

    async def get_hash(self, key: str, field: str) -> Optional[Any]:
        """Get hash field value"""
        try:
            value = await self.client.hget(key, field)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.warning("Redis hget failed", key=key, field=field, error=str(e))
            return None

    async def get_all_hash(self, key: str) -> dict:
        """Get all hash fields and values"""
        try:
            values = await self.client.hgetall(key)
            result = {}
            for field, value in values.items():
                try:
                    result[field] = json.loads(value)
                except json.JSONDecodeError:
                    result[field] = value
            return result
        except Exception as e:
            logger.warning("Redis hgetall failed", key=key, error=str(e))
            return {}

    async def delete_hash_field(self, key: str, field: str) -> bool:
        """Delete hash field"""
        try:
            result = await self.client.hdel(key, field)
            return result > 0
        except Exception as e:
            logger.warning("Redis hdel failed", key=key, field=field, error=str(e))
            return False

    async def add_to_set(self, key: str, value: str) -> bool:
        """Add value to set"""
        try:
            await self.client.sadd(key, value)
            return True
        except Exception as e:
            logger.warning("Redis sadd failed", key=key, error=str(e))
            return False

    async def get_set_members(self, key: str) -> set:
        """Get all set members"""
        try:
            return await self.client.smembers(key)
        except Exception as e:
            logger.warning("Redis smembers failed", key=key, error=str(e))
            return set()

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            logger.info("Redis client closed")


# Global Redis client instance
redis_client = RedisClient.get_instance()
