import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import redis
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RateLimiterService:
    """Redis-backed rate limiter and usage tracker"""

    def __init__(self):
        self.requests_per_window = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.window_size = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

        self.redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )

        logger.info(f"Rate limiter initialized: {self.requests_per_window} requests per {self.window_size}s")

    async def check_user_limit(self, username: str) -> bool:
        key = f"rate_limit:{username}"
        current_count = self.redis.get(key)

        if current_count is None:
            self.redis.set(key, 1, ex=self.window_size)
            return True
        elif int(current_count) < self.requests_per_window:
            self.redis.incr(key)
            return True
        else:
            logger.warning(f"Rate limit exceeded for user: {username}")
            return False

    async def record_usage(self, username: str) -> None:
        try:
            await self._update_user_stats(username)
            logger.debug(f"Recorded API usage for user: {username}")
        except Exception as e:
            logger.error(f"Error recording usage for {username}: {e}")

    async def get_user_stats(self, username: str) -> Dict[str, Any]:
        try:
            key = f"rate_limit:{username}"
            current_count = self.redis.get(key)
            ttl = self.redis.ttl(key)

            remaining = self.requests_per_window - int(current_count or 0)
            reset_time = datetime.utcnow() + timedelta(seconds=ttl if ttl > 0 else self.window_size)

            stats = {
                "requests_in_current_window": int(current_count or 0),
                "remaining_requests": max(0, remaining),
                "reset_time": reset_time.isoformat(),
                "window_size_seconds": self.window_size,
                "limit_per_window": self.requests_per_window
            }

            return stats
        except Exception as e:
            logger.error(f"Error getting stats for {username}: {e}")
            return {
                "requests_in_current_window": 0,
                "remaining_requests": self.requests_per_window,
                "error": "Unable to retrieve stats"
            }

    async def _update_user_stats(self, username: str) -> None:
        try:
            stats_key = f"user_stats:{username}"
            current_time = datetime.utcnow().isoformat()

            pipe = self.redis.pipeline()
            pipe.hincrby(stats_key, "total_requests", 1)
            pipe.hincrby(stats_key, "requests_today", 1)
            pipe.hset(stats_key, "last_request", current_time)
            pipe.hsetnx(stats_key, "first_request", current_time)
            pipe.execute()
        except Exception as e:
            logger.error(f"Error updating stats for {username}: {e}")

    async def get_rate_limit_info(self, username: str) -> Dict[str, Any]:
        try:
            stats = await self.get_user_stats(username)
            return {
                "X-RateLimit-Limit": str(self.requests_per_window),
                "X-RateLimit-Remaining": str(stats.get("remaining_requests", 0)),
                "X-RateLimit-Reset": stats.get("reset_time", ""),
                "X-RateLimit-Window": str(self.window_size)
            }
        except Exception as e:
            logger.error(f"Error getting rate limit info for {username}: {e}")
            return {}

    async def reset_user_limits(self, username: str) -> bool:
        try:
            self.redis.delete(f"rate_limit:{username}")
            logger.info(f"Rate limits reset for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Error resetting limits for {username}: {e}")
            return False

    async def get_global_stats(self) -> Dict[str, Any]:
        try:
            keys = self.redis.keys("rate_limit:*")
            total_users = len(keys)
            total_requests = sum(int(self.redis.get(k) or 0) for k in keys)

            return {
                "total_users": total_users,
                "total_requests_in_window": total_requests,
                "window_size_seconds": self.window_size,
                "limit_per_user": self.requests_per_window,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {"error": "Unable to retrieve global stats"}

    def cleanup_old_data(self) -> None:
        
        logger.debug("Redis handles cleanup via expiration")
