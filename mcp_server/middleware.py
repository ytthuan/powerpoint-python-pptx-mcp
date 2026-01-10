"""Middleware pipeline for MCP tool calls.

This module provides a middleware system for processing tool calls,
allowing for cross-cutting concerns like logging, validation, and metrics.
"""

import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional, Protocol, Awaitable

from .logging_config import get_logger, set_correlation_id
from .metrics import MetricsCollector
from .services import get_registry

logger = get_logger(__name__)


class Middleware(Protocol):
    """Protocol for middleware components.
    
    Middleware components can intercept and process tool calls,
    adding cross-cutting functionality like logging, validation, etc.
    """
    
    async def __call__(
        self,
        name: str,
        args: Dict[str, Any],
        next_handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process a tool call.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from the tool call
        """
        ...


class LoggingMiddleware:
    """Middleware for logging tool calls with correlation IDs.
    
    This middleware:
    - Generates correlation IDs for request tracing
    - Logs tool call start and completion
    - Logs execution time
    - Handles error logging
    """
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """Initialize logging middleware.
        
        Args:
            logger_instance: Optional logger instance to use
        """
        self.logger = logger_instance or logger
    
    async def __call__(
        self,
        name: str,
        args: Dict[str, Any],
        next_handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process tool call with logging.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from the tool call
        """
        # Generate and set correlation ID
        correlation_id = set_correlation_id()
        
        # Log tool call start
        self.logger.info(
            f"Tool call started: {name}",
            extra={
                "tool_name": name,
                "correlation_id": correlation_id,
                "tool_args": self._sanitize_args(args)
            }
        )
        
        start_time = time.time()
        
        try:
            result = await next_handler(name, args)
            
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.info(
                f"Tool call completed: {name} ({elapsed_ms:.2f}ms)",
                extra={
                    "tool_name": name,
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "success": True
                }
            )
            
            return result
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.error(
                f"Tool call failed: {name} ({elapsed_ms:.2f}ms) - {str(e)}",
                extra={
                    "tool_name": name,
                    "correlation_id": correlation_id,
                    "elapsed_ms": elapsed_ms,
                    "success": False,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def _sanitize_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize arguments for logging (remove sensitive data).
        
        Args:
            args: Arguments to sanitize
            
        Returns:
            Sanitized arguments
        """
        # For now, just return args as-is
        # In production, you might want to mask sensitive fields
        return args


class ValidationMiddleware:
    """Middleware for common input validation.
    
    This middleware validates common parameters before they reach
    the tool handlers, providing consistent error messages.
    """
    
    async def __call__(
        self,
        name: str,
        args: Dict[str, Any],
        next_handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process tool call with validation.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from the tool call
            
        Raises:
            ValueError: If validation fails
        """
        # Validate slide_number if present
        if "slide_number" in args:
            slide_number = args["slide_number"]
            if not isinstance(slide_number, int):
                raise ValueError(f"slide_number must be an integer, got {type(slide_number).__name__}")
            if slide_number < 1:
                raise ValueError(f"slide_number must be >= 1, got {slide_number}")
        
        # Validate pptx_path if present
        if "pptx_path" in args:
            pptx_path = args["pptx_path"]
            if not isinstance(pptx_path, str):
                raise ValueError(f"pptx_path must be a string, got {type(pptx_path).__name__}")
            if not pptx_path:
                raise ValueError("pptx_path cannot be empty")
        
        return await next_handler(name, args)


class MetricsMiddleware:
    """Middleware for collecting operation metrics.
    
    This middleware tracks:
    - Tool call counts
    - Execution times
    - Success/failure rates
    """
    
    def __init__(self):
        """Initialize metrics middleware."""
        self.metrics_collector: Optional[MetricsCollector] = None
        
        # Try to get metrics collector from registry
        try:
            registry = get_registry()
            self.metrics_collector = registry.resolve_optional(MetricsCollector)
        except Exception:
            # Metrics collector not available, continue without it
            pass
    
    async def __call__(
        self,
        name: str,
        args: Dict[str, Any],
        next_handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Process tool call with metrics collection.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            next_handler: Next handler in the pipeline
            
        Returns:
            Result from the tool call
        """
        if self.metrics_collector is None:
            # No metrics collector available, just pass through
            return await next_handler(name, args)
        
        start_time = time.time()
        
        try:
            result = await next_handler(name, args)
            
            elapsed_time = time.time() - start_time
            self.metrics_collector.record_operation(
                operation=f"tool.{name}",
                duration=elapsed_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.metrics_collector.record_operation(
                operation=f"tool.{name}",
                duration=elapsed_time,
                success=False
            )
            raise


class MiddlewarePipeline:
    """Pipeline for executing middleware in sequence.
    
    This class manages a chain of middleware components and executes
    them in order for each tool call.
    
    Example:
        pipeline = MiddlewarePipeline([
            LoggingMiddleware(),
            ValidationMiddleware(),
            MetricsMiddleware()
        ])
        
        result = await pipeline.execute("my_tool", args, handler)
    """
    
    def __init__(self, middlewares: list[Middleware]):
        """Initialize middleware pipeline.
        
        Args:
            middlewares: List of middleware components to execute in order
        """
        self.middlewares = middlewares
    
    async def execute(
        self,
        name: str,
        args: Dict[str, Any],
        handler: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Execute the middleware pipeline.
        
        Args:
            name: Name of the tool being called
            args: Arguments for the tool
            handler: Final handler to execute after all middleware
            
        Returns:
            Result from the tool call
        """
        if not self.middlewares:
            # No middleware, just call handler directly
            return await handler(name, args)
        
        # Build the middleware chain from right to left
        current_handler = handler
        
        for middleware in reversed(self.middlewares):
            # Capture the current handler in a closure
            def make_next_handler(mw, current):
                async def next_handler(n, a):
                    return await mw(n, a, current)
                return next_handler
            
            current_handler = make_next_handler(middleware, current_handler)
        
        # Execute the chain
        return await current_handler(name, args)
