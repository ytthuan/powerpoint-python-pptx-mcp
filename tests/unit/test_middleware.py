"""Tests for middleware pipeline."""

import asyncio
from unittest.mock import patch

import pytest

from mcp_server.middleware import (
    LoggingMiddleware,
    MetricsMiddleware,
    MiddlewarePipeline,
    ValidationMiddleware,
)


@pytest.fixture
def mock_handler():
    """Create a mock handler that returns a result."""

    async def handler(name, args):
        return {"result": "success", "tool": name, "args": args}

    return handler


@pytest.fixture
def error_handler():
    """Create a mock handler that raises an error."""

    async def handler(name, args):
        raise ValueError("Handler error")

    return handler


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware."""

    @pytest.mark.asyncio
    async def test_logs_tool_call(self, mock_handler):
        """Test that logging middleware logs tool calls."""
        import logging

        test_logger = logging.getLogger("test_middleware")
        test_logger.setLevel(logging.INFO)

        middleware = LoggingMiddleware(logger_instance=test_logger)

        with patch("mcp_server.middleware.set_correlation_id") as mock_set_corr:
            mock_set_corr.return_value = "test-corr-id"
            result = await middleware("test_tool", {"key": "value"}, mock_handler)

        assert result == {"result": "success", "tool": "test_tool", "args": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_logs_errors(self, error_handler):
        """Test that logging middleware logs errors."""
        import logging

        test_logger = logging.getLogger("test_middleware_error")
        test_logger.setLevel(logging.INFO)

        middleware = LoggingMiddleware(logger_instance=test_logger)

        with patch("mcp_server.middleware.set_correlation_id") as mock_set_corr:
            mock_set_corr.return_value = "test-corr-id"
            with pytest.raises(ValueError, match="Handler error"):
                await middleware("test_tool", {}, error_handler)

    @pytest.mark.asyncio
    async def test_correlation_id_generation(self, mock_handler):
        """Test that correlation ID is generated."""
        middleware = LoggingMiddleware()

        with patch("mcp_server.middleware.set_correlation_id") as mock_set_corr:
            mock_set_corr.return_value = "test-correlation-id"
            await middleware("test_tool", {}, mock_handler)

            mock_set_corr.assert_called_once()

    @pytest.mark.asyncio
    async def test_timing_logged(self, mock_handler):
        """Test that execution time is logged."""
        import logging

        test_logger = logging.getLogger("test_middleware_timing")
        test_logger.setLevel(logging.INFO)

        middleware = LoggingMiddleware(logger_instance=test_logger)

        # Add delay to handler
        async def delayed_handler(name, args):
            await asyncio.sleep(0.01)
            return await mock_handler(name, args)

        with patch("mcp_server.middleware.set_correlation_id") as mock_set_corr:
            mock_set_corr.return_value = "test-corr-id"
            await middleware("test_tool", {}, delayed_handler)


class TestValidationMiddleware:
    """Tests for ValidationMiddleware."""

    @pytest.mark.asyncio
    async def test_validates_slide_number_type(self, mock_handler):
        """Test that slide_number must be an integer."""
        middleware = ValidationMiddleware()

        with pytest.raises(ValueError, match="slide_number must be an integer"):
            await middleware("test_tool", {"slide_number": "not_a_number"}, mock_handler)

    @pytest.mark.asyncio
    async def test_validates_slide_number_positive(self, mock_handler):
        """Test that slide_number must be positive."""
        middleware = ValidationMiddleware()

        with pytest.raises(ValueError, match="slide_number must be >= 1"):
            await middleware("test_tool", {"slide_number": 0}, mock_handler)

    @pytest.mark.asyncio
    async def test_validates_pptx_path_type(self, mock_handler):
        """Test that pptx_path must be a string."""
        middleware = ValidationMiddleware()

        with pytest.raises(ValueError, match="pptx_path must be a string"):
            await middleware("test_tool", {"pptx_path": 123}, mock_handler)

    @pytest.mark.asyncio
    async def test_validates_pptx_path_not_empty(self, mock_handler):
        """Test that pptx_path cannot be empty."""
        middleware = ValidationMiddleware()

        with pytest.raises(ValueError, match="pptx_path cannot be empty"):
            await middleware("test_tool", {"pptx_path": ""}, mock_handler)

    @pytest.mark.asyncio
    async def test_passes_valid_arguments(self, mock_handler):
        """Test that valid arguments pass through."""
        middleware = ValidationMiddleware()

        result = await middleware(
            "test_tool", {"slide_number": 5, "pptx_path": "/path/to/file.pptx"}, mock_handler
        )

        assert result["result"] == "success"

    @pytest.mark.asyncio
    async def test_passes_arguments_without_validation_fields(self, mock_handler):
        """Test that arguments without validation fields pass through."""
        middleware = ValidationMiddleware()

        result = await middleware("test_tool", {"other_field": "value"}, mock_handler)

        assert result["result"] == "success"


class TestMetricsMiddleware:
    """Tests for MetricsMiddleware."""

    @pytest.mark.asyncio
    async def test_records_successful_operation(self, mock_handler):
        """Test that successful operations are recorded."""
        middleware = MetricsMiddleware()

        # Mock the metrics collector
        with patch.object(middleware, "metrics_collector") as mock_collector:
            await middleware("test_tool", {}, mock_handler)

            mock_collector.record_operation.assert_called_once()
            call_args = mock_collector.record_operation.call_args
            assert call_args[1]["operation"] == "tool.test_tool"
            assert call_args[1]["success"] is True
            assert "duration" in call_args[1]

    @pytest.mark.asyncio
    async def test_records_failed_operation(self, error_handler):
        """Test that failed operations are recorded."""
        middleware = MetricsMiddleware()

        # Mock the metrics collector
        with patch.object(middleware, "metrics_collector") as mock_collector:
            with pytest.raises(ValueError):
                await middleware("test_tool", {}, error_handler)

            mock_collector.record_operation.assert_called_once()
            call_args = mock_collector.record_operation.call_args
            assert call_args[1]["success"] is False

    @pytest.mark.asyncio
    async def test_works_without_metrics_collector(self, mock_handler):
        """Test that middleware works without metrics collector."""
        middleware = MetricsMiddleware()
        middleware.metrics_collector = None

        result = await middleware("test_tool", {}, mock_handler)
        assert result["result"] == "success"


class TestMiddlewarePipeline:
    """Tests for MiddlewarePipeline."""

    @pytest.mark.asyncio
    async def test_executes_single_middleware(self, mock_handler):
        """Test executing pipeline with single middleware."""
        calls = []

        async def tracking_middleware(name, args, next_handler):
            calls.append("before")
            result = await next_handler(name, args)
            calls.append("after")
            return result

        pipeline = MiddlewarePipeline([tracking_middleware])
        result = await pipeline.execute("test_tool", {}, mock_handler)

        assert result["result"] == "success"
        assert calls == ["before", "after"]

    @pytest.mark.asyncio
    async def test_executes_multiple_middlewares_in_order(self, mock_handler):
        """Test that middlewares execute in order."""
        calls = []

        async def middleware1(name, args, next_handler):
            calls.append("m1_before")
            result = await next_handler(name, args)
            calls.append("m1_after")
            return result

        async def middleware2(name, args, next_handler):
            calls.append("m2_before")
            result = await next_handler(name, args)
            calls.append("m2_after")
            return result

        pipeline = MiddlewarePipeline([middleware1, middleware2])
        await pipeline.execute("test_tool", {}, mock_handler)

        # Middlewares should execute in order: m1 -> m2 -> handler -> m2 -> m1
        assert calls == ["m1_before", "m2_before", "m2_after", "m1_after"]

    @pytest.mark.asyncio
    async def test_middleware_can_modify_result(self, mock_handler):
        """Test that middleware can modify results."""

        async def modifier_middleware(name, args, next_handler):
            result = await next_handler(name, args)
            result["modified"] = True
            return result

        pipeline = MiddlewarePipeline([modifier_middleware])
        result = await pipeline.execute("test_tool", {}, mock_handler)

        assert result["modified"] is True

    @pytest.mark.asyncio
    async def test_middleware_can_catch_errors(self, error_handler):
        """Test that middleware can catch and handle errors."""

        async def error_catching_middleware(name, args, next_handler):
            try:
                return await next_handler(name, args)
            except ValueError:
                return {"error": "caught"}

        pipeline = MiddlewarePipeline([error_catching_middleware])
        result = await pipeline.execute("test_tool", {}, error_handler)

        assert result == {"error": "caught"}

    @pytest.mark.asyncio
    async def test_empty_pipeline(self, mock_handler):
        """Test that empty pipeline just calls handler."""
        pipeline = MiddlewarePipeline([])
        result = await pipeline.execute("test_tool", {"key": "value"}, mock_handler)

        assert result == {"result": "success", "tool": "test_tool", "args": {"key": "value"}}

    @pytest.mark.asyncio
    async def test_integration_with_real_middlewares(self, mock_handler):
        """Test pipeline with actual middleware implementations."""
        pipeline = MiddlewarePipeline(
            [LoggingMiddleware(), ValidationMiddleware(), MetricsMiddleware()]
        )

        result = await pipeline.execute(
            "test_tool", {"slide_number": 1, "pptx_path": "/test.pptx"}, mock_handler
        )

        assert result["result"] == "success"
