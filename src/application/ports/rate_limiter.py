"""Rate limiter port (interface) for the application layer."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


class RateLimitResult:
    """Result of a rate limit check."""
    
    def __init__(
        self,
        allowed: bool,
        remaining: int,
        reset_time: int,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        self.allowed = allowed
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after
        self.limit = limit


class RateLimiter(ABC):
    """Rate limiter interface following hexagonal architecture."""
    
    @abstractmethod
    async def check_rate_limit(
        self,
        identifier: str,
        rate: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RateLimitResult:
        """
        Check if a request should be rate limited.
        
        Args:
            identifier: Unique identifier for the rate limit (IP, user ID, etc.)
            rate: Rate limit string (e.g., "100/minute", "10/second")
            strategy: Rate limiting strategy to use
            metadata: Additional metadata for the rate limit check
            
        Returns:
            RateLimitResult with information about the rate limit status
        """
        pass
    
    @abstractmethod
    async def reset_rate_limit(
        self,
        identifier: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
    ) -> bool:
        """
        Reset rate limit for a specific identifier.
        
        Args:
            identifier: Unique identifier to reset
            strategy: Rate limiting strategy
            
        Returns:
            True if reset was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_rate_limit_info(
        self,
        identifier: str,
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
    ) -> Optional[RateLimitResult]:
        """
        Get current rate limit information for an identifier.
        
        Args:
            identifier: Unique identifier to check
            strategy: Rate limiting strategy
            
        Returns:
            RateLimitResult with current status or None if not found
        """
        pass
