"""Rate limiting decorators for FastAPI routes."""

import functools
from typing import Callable, Optional, Any
from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.application.ports.rate_limiter import RateLimitStrategy
from src.infrastructure.dependencies import get_rate_limiter


def rate_limit(
    rate: str,
    per: str = "ip",
    error_message: str = "Rate limit exceeded",
    error_code: int = 429,
) -> Callable:
    """
    Decorator for rate limiting FastAPI routes.
    
    Args:
        rate: Rate limit string (e.g., "100/minute", "10/second")
        per: Rate limiting strategy ("ip", "user", "endpoint", "global")
        error_message: Custom error message for rate limit exceeded
        error_code: HTTP status code for rate limit exceeded
        
    Returns:
        Decorated function with rate limiting
    """
    
    # Map string strategies to enum values
    strategy_map = {
        "ip": RateLimitStrategy.PER_IP,
        "user": RateLimitStrategy.PER_USER,
        "endpoint": RateLimitStrategy.PER_ENDPOINT,
        "global": RateLimitStrategy.GLOBAL,
    }
    
    strategy = strategy_map.get(per, RateLimitStrategy.PER_IP)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and rate limiter from dependencies
            request: Optional[Request] = None
            rate_limiter = None
            
            # Find Request object in args/kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Try to get from kwargs
                request = kwargs.get('request')
            
            if not request:
                # If no request found, proceed without rate limiting
                return await func(*args, **kwargs)
            
            # Get rate limiter from dependency injection
            try:
                rate_limiter = await get_rate_limiter()
            except Exception:
                # If rate limiter is not available, proceed without rate limiting
                return await func(*args, **kwargs)
            
            # Determine identifier based on strategy
            identifier = _get_identifier(request, strategy)
            
            # Check rate limit
            result = await rate_limiter.check_rate_limit(
                identifier=identifier,
                rate=rate,
                strategy=strategy,
            )
            
            if not result.allowed:
                # Add rate limit headers
                headers = {
                    "X-RateLimit-Limit": str(result.limit) if result.limit else "0",
                    "X-RateLimit-Remaining": str(result.remaining),
                    "X-RateLimit-Reset": str(result.reset_time),
                }
                
                if result.retry_after:
                    headers["Retry-After"] = str(result.retry_after)
                
                raise HTTPException(
                    status_code=error_code,
                    detail=error_message,
                    headers=headers,
                )
            
            # Add rate limit headers to successful responses
            response = await func(*args, **kwargs)
            
            # If response is a Response object, add headers
            if hasattr(response, 'headers'):
                response.headers["X-RateLimit-Limit"] = str(result.limit) if result.limit else "0"
                response.headers["X-RateLimit-Remaining"] = str(result.remaining)
                response.headers["X-RateLimit-Reset"] = str(result.reset_time)
            
            return response
        
        return wrapper
    return decorator


def _get_identifier(request: Request, strategy: RateLimitStrategy) -> str:
    """
    Get identifier for rate limiting based on strategy.
    
    Args:
        request: FastAPI request object
        strategy: Rate limiting strategy
        
    Returns:
        Identifier string for rate limiting
    """
    if strategy == RateLimitStrategy.PER_IP:
        # Get client IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    elif strategy == RateLimitStrategy.PER_USER:
        # Try to get user ID from request
        # This assumes you have user authentication in place
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        # Fall back to IP if no user
        return _get_identifier(request, RateLimitStrategy.PER_IP)
    
    elif strategy == RateLimitStrategy.PER_ENDPOINT:
        # Use endpoint path as identifier
        return f"endpoint:{request.url.path}"
    
    elif strategy == RateLimitStrategy.GLOBAL:
        # Global rate limiting
        return "global"
    
    else:
        # Default to IP
        return _get_identifier(request, RateLimitStrategy.PER_IP)


# Convenience decorators for common use cases
def rate_limit_per_ip(rate: str) -> Callable:
    """Rate limit per IP address."""
    return rate_limit(rate, per="ip")


def rate_limit_per_user(rate: str) -> Callable:
    """Rate limit per authenticated user."""
    return rate_limit(rate, per="user")


def rate_limit_per_endpoint(rate: str) -> Callable:
    """Rate limit per endpoint."""
    return rate_limit(rate, per="endpoint")


def rate_limit_global(rate: str) -> Callable:
    """Global rate limiting."""
    return rate_limit(rate, per="global")
