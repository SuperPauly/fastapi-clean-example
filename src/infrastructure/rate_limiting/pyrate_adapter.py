"""PyrateLimiter adapter implementation."""

import asyncio
import time
from typing import Optional, Dict, Any
from pyrate_limiter import Limiter, Rate, Duration, InMemoryBucket

from src.application.ports.rate_limiter import (
    RateLimiter,
    RateLimitResult,
    RateLimitStrategy,
)


class PyrateLimiterAdapter(RateLimiter):
    """PyrateLimiter implementation of the RateLimiter interface."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize the PyrateLimiter adapter.
        
        Args:
            redis_url: Optional Redis URL for distributed rate limiting.
                      If None, uses in-memory storage.
        """
        self._limiters: Dict[str, Limiter] = {}
        self._redis_url = redis_url
        
    def _parse_rate(self, rate_str: str) -> Rate:
        """
        Parse rate string into PyrateLimiter Rate object.
        
        Args:
            rate_str: Rate string like "100/minute", "10/second"
            
        Returns:
            Rate object for PyrateLimiter
        """
        parts = rate_str.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate format: {rate_str}")
            
        limit = int(parts[0])
        duration_str = parts[1].lower()
        
        duration_map = {
            "second": Duration.SECOND,
            "minute": Duration.MINUTE,
            "hour": Duration.HOUR,
            "day": Duration.DAY,
        }
        
        if duration_str not in duration_map:
            raise ValueError(f"Unsupported duration: {duration_str}")
            
        return Rate(limit, duration_map[duration_str])
    
    def _get_limiter_key(
        self,
        identifier: str,
        rate: str,
        strategy: RateLimitStrategy,
    ) -> str:
        """Generate a unique key for the limiter."""
        return f"{strategy.value}:{rate}:{identifier}"
    
    def _get_or_create_limiter(
        self,
        identifier: str,
        rate: str,
        strategy: RateLimitStrategy,
    ) -> Limiter:
        """Get or create a limiter for the given parameters."""
        key = self._get_limiter_key(identifier, rate, strategy)
        
        if key not in self._limiters:
            rate_obj = self._parse_rate(rate)
            
            # Use in-memory bucket for now
            # TODO: Add Redis bucket support when redis_url is provided
            bucket = InMemoryBucket()
            
            self._limiters[key] = Limiter(rate_obj, bucket=bucket)
            
        return self._limiters[key]
    
    async def check_rate_limit(
        self,
        identifier: str,
        rate: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RateLimitResult:
        """Check if a request should be rate limited."""
        limiter = self._get_or_create_limiter(identifier, rate, strategy)
        
        # Run the synchronous rate limit check in a thread pool
        loop = asyncio.get_event_loop()
        
        def _check():
            try:
                # Try to acquire a token
                limiter.try_acquire(identifier)
                return True, None
            except Exception as e:
                return False, e
        
        allowed, error = await loop.run_in_executor(None, _check)
        
        # Get current bucket state
        def _get_state():
            try:
                bucket = limiter.bucket
                # Get remaining tokens (this is an approximation)
                # PyrateLimiter doesn't expose remaining tokens directly
                remaining = 0  # Default to 0 for now
                reset_time = int(time.time()) + 60  # Default to 1 minute
                return remaining, reset_time
            except Exception:
                return 0, int(time.time()) + 60
        
        remaining, reset_time = await loop.run_in_executor(None, _get_state)
        
        retry_after = None
        if not allowed:
            retry_after = 60  # Default retry after 60 seconds
            
        # Parse rate to get limit
        rate_obj = self._parse_rate(rate)
        limit = rate_obj.limit
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            limit=limit,
        )
    
    async def reset_rate_limit(
        self,
        identifier: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
    ) -> bool:
        """Reset rate limit for a specific identifier."""
        # Find all limiters for this identifier and strategy
        keys_to_remove = [
            key for key in self._limiters.keys()
            if key.startswith(f"{strategy.value}:") and key.endswith(f":{identifier}")
        ]
        
        for key in keys_to_remove:
            del self._limiters[key]
            
        return len(keys_to_remove) > 0
    
    async def get_rate_limit_info(
        self,
        identifier: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
    ) -> Optional[RateLimitResult]:
        """Get current rate limit information for an identifier."""
        # Find a limiter for this identifier and strategy
        matching_keys = [
            key for key in self._limiters.keys()
            if key.startswith(f"{strategy.value}:") and key.endswith(f":{identifier}")
        ]
        
        if not matching_keys:
            return None
            
        # Use the first matching limiter
        key = matching_keys[0]
        limiter = self._limiters[key]
        
        # Extract rate from key
        parts = key.split(":")
        if len(parts) >= 2:
            rate = parts[1]
        else:
            rate = "100/minute"  # Default
            
        # Get current state without consuming a token
        loop = asyncio.get_event_loop()
        
        def _get_info():
            try:
                remaining = 0  # PyrateLimiter doesn't expose this easily
                reset_time = int(time.time()) + 60
                return remaining, reset_time
            except Exception:
                return 0, int(time.time()) + 60
        
        remaining, reset_time = await loop.run_in_executor(None, _get_info)
        
        rate_obj = self._parse_rate(rate)
        
        return RateLimitResult(
            allowed=True,  # This is just info, not a check
            remaining=remaining,
            reset_time=reset_time,
            limit=rate_obj.limit,
        )
