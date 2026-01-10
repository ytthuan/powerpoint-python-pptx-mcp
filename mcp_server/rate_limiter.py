"""Rate limiting implementation for MCP server.

This module provides a token bucket rate limiter to prevent abuse
and ensure fair resource usage.
"""

import asyncio
import logging
import time
from typing import Dict, Optional

from .config import get_config
from .exceptions import PPTXError

logger = logging.getLogger(__name__)


class RateLimitError(PPTXError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None
    ):
        """Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message)
        self.retry_after = retry_after


class TokenBucketRateLimiter:
    """Token bucket rate limiter implementation.
    
    This rate limiter uses the token bucket algorithm to limit
    the rate of operations. Tokens are added to the bucket at a
    constant rate, and operations consume tokens.
    
    Example:
        limiter = TokenBucketRateLimiter(
            rate=60,  # 60 requests per minute
            per=60.0  # per 60 seconds
        )
        
        async def handle_request():
            await limiter.acquire()  # Wait for token
            # Process request
    """
    
    def __init__(
        self,
        rate: int,
        per: float = 60.0,
        burst: Optional[int] = None
    ):
        """Initialize token bucket rate limiter.
        
        Args:
            rate: Number of tokens to add per time period
            per: Time period in seconds (default: 60 seconds)
            burst: Maximum number of tokens in bucket (default: same as rate)
        """
        self.rate = rate
        self.per = per
        self.burst = burst or rate
        
        # Token bucket state
        self._tokens = float(self.burst)
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
        
        logger.info(
            f"Rate limiter initialized: {rate} requests per {per} seconds "
            f"(burst: {self.burst})"
        )
    
    def _add_tokens(self) -> None:
        """Add tokens to the bucket based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        
        # Calculate tokens to add
        tokens_to_add = elapsed * (self.rate / self.per)
        
        # Update token count (capped at burst limit)
        self._tokens = min(self.burst, self._tokens + tokens_to_add)
        self._last_update = now
    
    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens from the bucket.
        
        This method blocks until enough tokens are available.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Raises:
            ValueError: If tokens exceeds burst limit
        """
        if tokens > self.burst:
            raise ValueError(
                f"Requested {tokens} tokens exceeds burst limit of {self.burst}"
            )
        
        async with self._lock:
            while True:
                self._add_tokens()
                
                if self._tokens >= tokens:
                    # Enough tokens available
                    self._tokens -= tokens
                    return
                
                # Not enough tokens, calculate wait time
                tokens_needed = tokens - self._tokens
                wait_time = tokens_needed * (self.per / self.rate)
                
                # Release lock while waiting
                logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            True if tokens were acquired, False otherwise
            
        Raises:
            ValueError: If tokens exceeds burst limit
        """
        if tokens > self.burst:
            raise ValueError(
                f"Requested {tokens} tokens exceeds burst limit of {self.burst}"
            )
        
        async with self._lock:
            self._add_tokens()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def get_available_tokens(self) -> float:
        """Get the current number of available tokens.
        
        Returns:
            Number of available tokens
        """
        # Note: This is not thread-safe but provides an estimate
        now = time.monotonic()
        elapsed = now - self._last_update
        tokens_to_add = elapsed * (self.rate / self.per)
        return min(self.burst, self._tokens + tokens_to_add)
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time for acquiring tokens.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            
        Returns:
            Estimated wait time in seconds (0 if tokens available)
        """
        available = self.get_available_tokens()
        if available >= tokens:
            return 0.0
        
        tokens_needed = tokens - available
        return tokens_needed * (self.per / self.rate)


class RateLimiterMiddleware:
    """Middleware for rate limiting tool calls.
    
    This middleware uses a token bucket rate limiter to limit
    the rate of tool calls.
    """
    
    def __init__(self, limiter: Optional[TokenBucketRateLimiter] = None):
        """Initialize rate limiter middleware.
        
        Args:
            limiter: Optional rate limiter instance. If None, creates one from config.
        """
        if limiter is None:
            config = get_config()
            if config.performance.enable_rate_limiting:
                self.limiter = TokenBucketRateLimiter(
                    rate=config.performance.max_requests_per_minute,
                    per=60.0
                )
            else:
                self.limiter = None
        else:
            self.limiter = limiter
    
    async def __call__(self, name, args, next_handler):
        """Process tool call with rate limiting.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from the tool call
            
        Raises:
            RateLimitError: If rate limit is exceeded
        """
        if self.limiter is None:
            # Rate limiting disabled
            return await next_handler(name, args)
        
        # Try to acquire token
        acquired = await self.limiter.try_acquire()
        
        if not acquired:
            wait_time = self.limiter.get_wait_time()
            logger.warning(
                f"Rate limit exceeded for tool: {name}. "
                f"Retry after {wait_time:.2f}s"
            )
            raise RateLimitError(
                message=f"Rate limit exceeded. Please retry after {wait_time:.2f} seconds.",
                retry_after=wait_time
            )
        
        return await next_handler(name, args)


# Global rate limiter instance
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter() -> Optional[TokenBucketRateLimiter]:
    """Get the global rate limiter instance.
    
    Returns:
        The global rate limiter instance, or None if disabled
    """
    global _rate_limiter
    
    if _rate_limiter is None:
        config = get_config()
        if config.performance.enable_rate_limiting:
            _rate_limiter = TokenBucketRateLimiter(
                rate=config.performance.max_requests_per_minute,
                per=60.0
            )
    
    return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the global rate limiter (useful for testing)."""
    global _rate_limiter
    _rate_limiter = None
