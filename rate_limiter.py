import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class RateLimiterService:
    """Service for implementing rate limiting and usage tracking"""
    
    def __init__(self):
        
        self.requests_per_window = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.window_size = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))  
        
        
        self.user_requests: Dict[str, deque] = defaultdict(deque)
        self.user_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        logger.info(f"Rate limiter initialized: {self.requests_per_window} requests per {self.window_size}s")
    
    async def check_user_limit(self, username: str) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            username: Username to check
            
        Returns:
            True if request is allowed, False if rate limited
        """
        try:
            current_time = time.time()
            user_queue = self.user_requests[username]
            
            
            while user_queue and user_queue[0] <= current_time - self.window_size:
                user_queue.popleft()
            
            
            if len(user_queue) >= self.requests_per_window:
                logger.warning(f"Rate limit exceeded for user: {username}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit for {username}: {e}")
            return True  
    
    async def record_usage(self, username: str) -> None:
        """
        Record a successful API usage
        
        Args:
            username: Username to record usage for
        """
        try:
            current_time = time.time()
            
            
            self.user_requests[username].append(current_time)
            
            
            await self._update_user_stats(username)
            
            logger.debug(f"Recorded API usage for user: {username}")
            
        except Exception as e:
            logger.error(f"Error recording usage for {username}: {e}")
    
    async def get_user_stats(self, username: str) -> Dict[str, Any]:
        """
        Get usage statistics for a user
        
        Args:
            username: Username to get stats for
            
        Returns:
            Dictionary containing user statistics
        """
        try:
            current_time = time.time()
            user_queue = self.user_requests[username]
            
            
            while user_queue and user_queue[0] <= current_time - self.window_size:
                user_queue.popleft()
            
            
            requests_in_window = len(user_queue)
            remaining_requests = max(0, self.requests_per_window - requests_in_window)
            
            
            reset_time = None
            if user_queue:
                oldest_request = user_queue[0]
                reset_time = datetime.fromtimestamp(oldest_request + self.window_size)
            else:
                reset_time = datetime.utcnow()
            
            
            user_stats = self.user_stats.get(username, {})
            
            stats = {
                "requests_in_current_window": requests_in_window,
                "remaining_requests": remaining_requests,
                "reset_time": reset_time.isoformat(),
                "window_size_seconds": self.window_size,
                "limit_per_window": self.requests_per_window,
                "requests_today": user_stats.get("requests_today", 0),
                "total_requests": user_stats.get("total_requests", 0),
                "first_request": user_stats.get("first_request"),
                "last_request": user_stats.get("last_request")
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
        """Update user statistics"""
        try:
            current_time = datetime.utcnow()
            current_date = current_time.date()
            
            
            if username not in self.user_stats:
                self.user_stats[username] = {
                    "total_requests": 0,
                    "requests_today": 0,
                    "last_request_date": None,
                    "first_request": current_time.isoformat(),
                    "last_request": None
                }
            
            stats = self.user_stats[username]
            
            
            last_request_date = stats.get("last_request_date")
            if not last_request_date or last_request_date != current_date:
                stats["requests_today"] = 0
                stats["last_request_date"] = current_date
            
            
            stats["total_requests"] += 1
            stats["requests_today"] += 1
            stats["last_request"] = current_time.isoformat()
            
        except Exception as e:
            logger.error(f"Error updating stats for {username}: {e}")
    
    async def get_rate_limit_info(self, username: str) -> Dict[str, Any]:
        """
        Get rate limit information for response headers
        
        Args:
            username: Username to get info for
            
        Returns:
            Rate limit information
        """
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
        """
        Reset rate limits for a user (admin function)
        
        Args:
            username: Username to reset limits for
            
        Returns:
            True if successful
        """
        try:
            if username in self.user_requests:
                self.user_requests[username].clear()
            
            logger.info(f"Rate limits reset for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error resetting limits for {username}: {e}")
            return False
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global rate limiting statistics"""
        try:
            total_users = len(self.user_requests)
            active_users = sum(1 for queue in self.user_requests.values() if queue)
            total_requests_in_window = sum(len(queue) for queue in self.user_requests.values())
            
            return {
                "total_users": total_users,
                "active_users_in_window": active_users,
                "total_requests_in_window": total_requests_in_window,
                "window_size_seconds": self.window_size,
                "limit_per_user": self.requests_per_window,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting global stats: {e}")
            return {"error": "Unable to retrieve global stats"}
    
    def cleanup_old_data(self) -> None:
        """Clean up old rate limiting data"""
        try:
            current_time = time.time()
            cutoff_time = current_time - (self.window_size * 2)  
            
            
            for username, queue in list(self.user_requests.items()):
                while queue and queue[0] <= cutoff_time:
                    queue.popleft()
                
                
                if not queue:
                    del self.user_requests[username]
            
            logger.debug("Cleaned up old rate limiting data")
            
        except Exception as e:
            logger.error(f"Error cleaning up rate limiting data: {e}")
