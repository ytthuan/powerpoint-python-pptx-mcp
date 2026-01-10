"""Integration test for MCP server architecture improvements.

This test demonstrates the complete flow of the improved architecture,
showing how all components work together.
"""

import asyncio
import logging
import pytest

# Import from server to trigger tool registration
import mcp_server.server  # noqa: F401
from mcp_server.server import middleware_pipeline
from mcp_server.tools.registry import get_tool_registry
from mcp_server.config import get_config


@pytest.mark.asyncio
async def test_architecture_integration():
    """Test that all architectural components work together."""
    # 1. Configuration
    config = get_config()
    assert config is not None

    # 2. Tool Registry
    registry = get_tool_registry()
    tools = registry.get_registered_tools()
    assert len(tools) == 24, f"Expected 24 tools, got {len(tools)}"
    assert registry.is_registered("health_check"), "health_check should be registered"

    # 3. Direct registry dispatch
    result = await registry.dispatch(
        "health_check", {"include_metrics": False, "include_cache_stats": False}
    )
    assert result["status"] == "healthy"
    assert result["server"] == "PPTX MCP Server"

    # 4. Middleware pipeline
    assert len(middleware_pipeline.middlewares) == 4

    # 5. Full flow through middleware
    result = await middleware_pipeline.execute(
        "health_check", {"include_metrics": False, "include_cache_stats": False}, registry.dispatch
    )
    assert result["status"] == "healthy"

    print("✅ All integration tests passed!")


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(test_architecture_integration())
