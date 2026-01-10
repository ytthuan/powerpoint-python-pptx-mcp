"""Health check and monitoring tools for MCP server."""

import time
from datetime import datetime, timezone
from typing import Any, Dict

from mcp.types import Tool

from ..cache import PresentationCache
from ..config import get_config
from ..metrics import MetricsCollector
from ..services import get_registry


def get_health_tools() -> list[Tool]:
    """Get health check and monitoring tools."""
    return [
        Tool(
            name="health_check",
            description="Check the health status of the MCP server including cache, config, and metrics",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_metrics": {
                        "type": "boolean",
                        "description": "Include detailed metrics in response (default: true)",
                        "default": True,
                    },
                    "include_cache_stats": {
                        "type": "boolean",
                        "description": "Include cache statistics in response (default: true)",
                        "default": True,
                    },
                },
                "required": [],
            },
        ),
    ]


async def handle_health_check(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle health check request.

    Args:
        arguments: Arguments containing optional flags for included information

    Returns:
        Dictionary with health status and optional detailed information
    """
    include_metrics = arguments.get("include_metrics", True)
    include_cache_stats = arguments.get("include_cache_stats", True)

    start_time = time.time()

    # Basic health status
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": "PPTX MCP Server",
        "version": "1.0.0",
    }

    # Check configuration
    try:
        config = get_config()
        health_status["config"] = {
            "environment": config.environment.value,
            "cache_enabled": config.performance.enable_cache,
            "max_file_size_gb": config.security.max_file_size / (1024**3),
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["errors"] = health_status.get("errors", [])
        health_status["errors"].append(f"Config error: {str(e)}")

    # Check cache if requested
    if include_cache_stats:
        try:
            # Try to get cache from registry
            registry = get_registry()
            cache = registry.resolve_optional(PresentationCache)
            if cache:
                health_status["cache"] = cache.get_stats()
            else:
                health_status["cache"] = {"status": "not initialized"}
        except Exception as e:
            health_status["cache"] = {"error": str(e)}

    # Include metrics if requested
    if include_metrics:
        try:
            registry = get_registry()
            collector = registry.resolve_optional(MetricsCollector)
            if collector:
                health_status["metrics"] = collector.get_metrics()
            else:
                health_status["metrics"] = {"status": "not initialized"}
        except Exception as e:
            health_status["metrics"] = {"error": str(e)}

    # Add response time
    response_time_ms = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = round(response_time_ms, 2)

    return health_status
