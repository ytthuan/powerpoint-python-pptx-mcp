"""Tests for rate limiter."""

import asyncio
import pytest
import time
from unittest.mock import patch

from mcp_server.rate_limiter import (
    TokenBucketRateLimiter,
    RateLimitError,
    RateLimiterMiddleware,
    get_rate_limiter,
    reset_rate_limiter,
)
from mcp_server.config import Config


@pytest.fixture(autouse=True)
def cleanup_rate_limiter():
    """Clean up global rate limiter after each test."""
    yield
    reset_rate_limiter()


class TestTokenBucketRateLimiter:
    """Tests for TokenBucketRateLimiter."""

    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=20)

        assert limiter.rate == 10
        assert limiter.per == 1.0
        assert limiter.burst == 20
        assert limiter._tokens == 20.0

    def test_default_burst(self):
        """Test that burst defaults to rate."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0)
        assert limiter.burst == 10

    @pytest.mark.asyncio
    async def test_acquire_single_token(self):
        """Test acquiring a single token."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0)

        # Should acquire immediately
        start = time.monotonic()
        await limiter.acquire(1)
        elapsed = time.monotonic() - start

        assert elapsed < 0.1  # Should be almost instant

    @pytest.mark.asyncio
    async def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens at once."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        await limiter.acquire(5)
        assert limiter._tokens == 5.0

    @pytest.mark.asyncio
    async def test_acquire_blocks_when_no_tokens(self):
        """Test that acquire blocks when tokens are exhausted."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)

        # Exhaust all tokens
        await limiter.acquire(5)

        # Next acquire should block
        start = time.monotonic()
        await limiter.acquire(1)
        elapsed = time.monotonic() - start

        # Should wait at least 0.1 seconds (1 token at 10/sec rate)
        assert elapsed >= 0.08  # Allow small margin

    @pytest.mark.asyncio
    async def test_try_acquire_success(self):
        """Test try_acquire returns True when tokens available."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        result = await limiter.try_acquire(5)
        assert result is True
        assert limiter._tokens == 5.0

    @pytest.mark.asyncio
    async def test_try_acquire_failure(self):
        """Test try_acquire returns False when tokens unavailable."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)

        # Exhaust all tokens
        await limiter.acquire(5)

        # Try to acquire more - should fail immediately
        result = await limiter.try_acquire(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_acquire_exceeds_burst_raises_error(self):
        """Test that requesting more tokens than burst raises error."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)

        with pytest.raises(ValueError, match="exceeds burst limit"):
            await limiter.acquire(10)

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self):
        """Test that tokens are refilled over time."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        # Exhaust tokens
        await limiter.acquire(10)
        assert limiter._tokens == 0.0

        # Wait for tokens to refill
        await asyncio.sleep(0.5)

        # Should have ~5 tokens now (10 per second * 0.5 seconds)
        available = limiter.get_available_tokens()
        assert 4.0 <= available <= 6.0  # Allow some margin

    @pytest.mark.asyncio
    async def test_tokens_capped_at_burst(self):
        """Test that tokens don't exceed burst limit."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)

        # Wait long enough to generate more than burst
        await asyncio.sleep(1.0)

        available = limiter.get_available_tokens()
        assert available <= 5.0

    def test_get_available_tokens(self):
        """Test getting available tokens."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        available = limiter.get_available_tokens()
        assert available == 10.0

    def test_get_wait_time_no_wait(self):
        """Test wait time when tokens are available."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        wait_time = limiter.get_wait_time(5)
        assert wait_time == 0.0

    def test_get_wait_time_with_wait(self):
        """Test wait time calculation when tokens unavailable."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)
        limiter._tokens = 0.0

        wait_time = limiter.get_wait_time(5)
        assert 0.4 <= wait_time <= 0.6  # ~0.5 seconds for 5 tokens at 10/sec

    @pytest.mark.asyncio
    async def test_concurrent_acquires(self):
        """Test that concurrent acquires are properly serialized."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)

        async def acquire_tokens():
            await limiter.acquire(3)
            return limiter._tokens

        # Start multiple concurrent acquire operations
        tasks = [acquire_tokens() for _ in range(3)]
        await asyncio.gather(*tasks)

        # After 3 acquires of 3 tokens each, should have 1 token left
        # (or be in the process of refilling)
        assert limiter._tokens <= 2.0


class TestRateLimiterMiddleware:
    """Tests for RateLimiterMiddleware."""

    @pytest.mark.asyncio
    async def test_middleware_with_rate_limiting_disabled(self):
        """Test that middleware passes through when rate limiting disabled."""
        config = Config()
        config.performance.enable_rate_limiting = False

        with patch("mcp_server.rate_limiter.get_config", return_value=config):
            middleware = RateLimiterMiddleware()

            async def handler(name, args):
                return {"result": "success"}

            result = await middleware("test_tool", {}, handler)
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_middleware_allows_within_limit(self):
        """Test that middleware allows requests within rate limit."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=10)
        middleware = RateLimiterMiddleware(limiter=limiter)

        async def handler(name, args):
            return {"result": "success"}

        # Should succeed
        result = await middleware("test_tool", {}, handler)
        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_middleware_blocks_exceeding_limit(self):
        """Test that middleware blocks when rate limit exceeded."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)
        middleware = RateLimiterMiddleware(limiter=limiter)

        async def handler(name, args):
            return {"result": "success"}

        # Exhaust all tokens
        await limiter.acquire(5)

        # Next request should raise RateLimitError
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            await middleware("test_tool", {}, handler)

    @pytest.mark.asyncio
    async def test_middleware_error_includes_retry_after(self):
        """Test that rate limit error includes retry_after."""
        limiter = TokenBucketRateLimiter(rate=10, per=1.0, burst=5)
        middleware = RateLimiterMiddleware(limiter=limiter)

        async def handler(name, args):
            return {"result": "success"}

        # Exhaust all tokens
        await limiter.acquire(5)

        try:
            await middleware("test_tool", {}, handler)
            pytest.fail("Should have raised RateLimitError")
        except RateLimitError as e:
            assert e.retry_after is not None
            assert e.retry_after > 0


class TestGlobalRateLimiter:
    """Tests for global rate limiter functions."""

    def test_get_rate_limiter_with_enabled(self):
        """Test getting rate limiter when enabled in config."""
        config = Config()
        config.performance.enable_rate_limiting = True
        config.performance.max_requests_per_minute = 60

        with patch("mcp_server.rate_limiter.get_config", return_value=config):
            limiter = get_rate_limiter()
            assert limiter is not None
            assert limiter.rate == 60
            assert limiter.per == 60.0

    def test_get_rate_limiter_with_disabled(self):
        """Test getting rate limiter when disabled in config."""
        config = Config()
        config.performance.enable_rate_limiting = False

        with patch("mcp_server.rate_limiter.get_config", return_value=config):
            limiter = get_rate_limiter()
            assert limiter is None

    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns same instance."""
        config = Config()
        config.performance.enable_rate_limiting = True

        with patch("mcp_server.rate_limiter.get_config", return_value=config):
            limiter1 = get_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is limiter2

    def test_reset_rate_limiter(self):
        """Test resetting global rate limiter."""
        config = Config()
        config.performance.enable_rate_limiting = True

        with patch("mcp_server.rate_limiter.get_config", return_value=config):
            limiter1 = get_rate_limiter()
            reset_rate_limiter()
            limiter2 = get_rate_limiter()
            assert limiter1 is not limiter2
