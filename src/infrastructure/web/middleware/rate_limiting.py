"""Rate limiting middleware for FastAPI."""

from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.application.ports.rate_limiter import RateLimitStrategy
from src.infrastructure.dependencies import get_rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting middleware.
    
    This middleware applies rate limiting to all requests based on configuration.
    """
    
    def __init__(
        self,
        app,
        default_rate: str = "100/minute",
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
        exclude_paths: Optional[list] = None,
        rate_limit_config: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application instance
            default_rate: Default rate limit for all endpoints
            strategy: Default rate limiting strategy
            exclude_paths: List of paths to exclude from rate limiting
            rate_limit_config: Per-path rate limit configuration
        """
        super().__init__(app)
        self.default_rate = default_rate
        self.strategy = strategy
        self.exclude_paths = exclude_paths or []
        self.rate_limit_config = rate_limit_config or {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        
        # Check if path should be excluded
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Get rate limiter
        try:
            rate_limiter = await get_rate_limiter()
        except Exception:
            # If rate limiter is not available, proceed without rate limiting
            return await call_next(request)
        
        # Determine rate limit for this path
        rate = self._get_rate_for_path(request.url.path)
        
        # Get identifier based on strategy
        identifier = self._get_identifier(request, self.strategy)
        
        # Check rate limit
        result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            rate=rate,
            strategy=self.strategy,
        )
        
        if not result.allowed:
            # Return rate limit exceeded response
            headers = {
                "X-RateLimit-Limit": str(result.limit) if result.limit else "0",
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_time),
            }
            
            if result.retry_after:
                headers["Retry-After"] = str(result.retry_after)
            
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(result.limit) if result.limit else "0"
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_time)
        
        return response
    
    def _should_exclude_path(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting."""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    def _get_rate_for_path(self, path: str) -> str:
        """Get rate limit for specific path."""
        # Check for exact match first
        if path in self.rate_limit_config:
            return self.rate_limit_config[path]
        
        # Check for prefix matches
        for config_path, rate in self.rate_limit_config.items():
            if path.startswith(config_path):
                return rate
        
        # Return default rate
        return self.default_rate
    
    def _get_identifier(self, request: Request, strategy: RateLimitStrategy) -> str:
        """Get identifier for rate limiting based on strategy."""
        if strategy == RateLimitStrategy.PER_IP:
            # Get client IP address
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        
        elif strategy == RateLimitStrategy.PER_USER:
            # Try to get user ID from request
            user_id = getattr(request.state, 'user_id', None)
            if user_id:
                return f"user:{user_id}"
            # Fall back to IP if no user
            return self._get_identifier(request, RateLimitStrategy.PER_IP)
        
        elif strategy == RateLimitStrategy.PER_ENDPOINT:
            # Use endpoint path as identifier
            return f"endpoint:{request.url.path}"
        
        elif strategy == RateLimitStrategy.GLOBAL:
            # Global rate limiting
            return "global"
        
        else:
            # Default to IP
            return self._get_identifier(request, RateLimitStrategy.PER_IP)


class SmartRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Smart rate limiting middleware with different limits for different endpoint types.
    """
    
    def __init__(
        self,
        app,
        api_rate: str = "100/minute",
        web_rate: str = "200/minute",
        static_rate: str = "1000/minute",
        strategy: RateLimitStrategy = RateLimitStrategy.PER_IP,
    ):
        """
        Initialize smart rate limiting middleware.
        
        Args:
            app: FastAPI application instance
            api_rate: Rate limit for API endpoints (/api/*)
            web_rate: Rate limit for web pages
            static_rate: Rate limit for static files
            strategy: Rate limiting strategy
        """
        super().__init__(app)
        self.api_rate = api_rate
        self.web_rate = web_rate
        self.static_rate = static_rate
        self.strategy = strategy
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with smart rate limiting."""
        
        # Determine rate based on path type
        path = request.url.path
        rate = self._get_smart_rate(path)
        
        # Get rate limiter
        try:
            rate_limiter = await get_rate_limiter()
        except Exception:
            # If rate limiter is not available, proceed without rate limiting
            return await call_next(request)
        
        # Get identifier
        identifier = self._get_identifier(request, self.strategy)
        
        # Check rate limit
        result = await rate_limiter.check_rate_limit(
            identifier=identifier,
            rate=rate,
            strategy=self.strategy,
        )
        
        if not result.allowed:
            headers = {
                "X-RateLimit-Limit": str(result.limit) if result.limit else "0",
                "X-RateLimit-Remaining": str(result.remaining),
                "X-RateLimit-Reset": str(result.reset_time),
            }
            
            if result.retry_after:
                headers["Retry-After"] = str(result.retry_after)
            
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers=headers,
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(result.limit) if result.limit else "0"
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_time)
        
        return response
    
    def _get_smart_rate(self, path: str) -> str:
        """Determine rate limit based on path type."""
        if path.startswith("/api/"):
            return self.api_rate
        elif path.startswith("/static/") or path.endswith((".css", ".js", ".png", ".jpg", ".ico")):
            return self.static_rate
        else:
            return self.web_rate
    
    def _get_identifier(self, request: Request, strategy: RateLimitStrategy) -> str:
        """Get identifier for rate limiting based on strategy."""
        if strategy == RateLimitStrategy.PER_IP:
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        
        elif strategy == RateLimitStrategy.PER_USER:
            user_id = getattr(request.state, 'user_id', None)
            if user_id:
                return f"user:{user_id}"
            return self._get_identifier(request, RateLimitStrategy.PER_IP)
        
        elif strategy == RateLimitStrategy.PER_ENDPOINT:
            return f"endpoint:{request.url.path}"
        
        elif strategy == RateLimitStrategy.GLOBAL:
            return "global"
        
        else:
            return self._get_identifier(request, RateLimitStrategy.PER_IP)
