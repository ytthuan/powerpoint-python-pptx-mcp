"""Main MCP server entry point."""

import asyncio
import logging
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

from .config import get_config
from .tools.read_tools import (
    get_read_tools,
    handle_read_slide_content,
    handle_read_slide_text,
    handle_read_slide_images,
    handle_read_presentation_info,
    handle_read_slides_metadata,
)
from .tools.edit_tools import (
    get_edit_tools,
    handle_update_slide_text,
    handle_replace_slide_image,
    handle_add_text_box,
    handle_add_image,
    handle_replace_slide_content,
    handle_update_slide_content,
)
from .tools.slide_tools import (
    get_slide_tools,
    handle_add_slide,
    handle_delete_slide,
    handle_duplicate_slide,
    handle_change_slide_layout,
    handle_set_slide_visibility,
)
from .tools.notes_tools import (
    get_notes_tools,
    handle_read_notes,
    handle_update_notes,
    handle_format_notes_structure,
    handle_read_notes_batch,
    handle_update_notes_batch,
    handle_process_notes_workflow,
)
from .tools.text_replace_tools import (
    get_text_replace_tools,
    handle_replace_text,
)
from .tools.health_tools import (
    get_health_tools,
    handle_health_check,
)
from .tools.registry import get_tool_registry
from .middleware import (
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    MetricsMiddleware,
)
from .rate_limiter import RateLimiterMiddleware
from .resources.pptx_resources import list_pptx_resources, get_pptx_resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("pptx-mcp-server")


# Initialize tool registry and register all tools
def register_all_tools():
    """Register all tool handlers with the tool registry."""
    registry = get_tool_registry()

    # Read tools
    registry.register_handler("read_slide_content", handle_read_slide_content)
    registry.register_handler("read_slide_text", handle_read_slide_text)
    registry.register_handler("read_slide_images", handle_read_slide_images)
    registry.register_handler("read_presentation_info", handle_read_presentation_info)
    registry.register_handler("read_slides_metadata", handle_read_slides_metadata)

    # Edit tools
    registry.register_handler("update_slide_text", handle_update_slide_text)
    registry.register_handler("replace_slide_image", handle_replace_slide_image)
    registry.register_handler("add_text_box", handle_add_text_box)
    registry.register_handler("add_image", handle_add_image)
    registry.register_handler("replace_slide_content", handle_replace_slide_content)
    registry.register_handler("update_slide_content", handle_update_slide_content)

    # Slide management tools
    registry.register_handler("add_slide", handle_add_slide)
    registry.register_handler("delete_slide", handle_delete_slide)
    registry.register_handler("duplicate_slide", handle_duplicate_slide)
    registry.register_handler("change_slide_layout", handle_change_slide_layout)
    registry.register_handler("set_slide_visibility", handle_set_slide_visibility)

    # Notes tools
    registry.register_handler("read_notes", handle_read_notes)
    registry.register_handler("read_notes_batch", handle_read_notes_batch)
    registry.register_handler("update_notes", handle_update_notes)
    registry.register_handler("update_notes_batch", handle_update_notes_batch)
    registry.register_handler("format_notes_structure", handle_format_notes_structure)
    registry.register_handler("process_notes_workflow", handle_process_notes_workflow)

    # Text replacement tools
    registry.register_handler("replace_text", handle_replace_text)

    # Health tools
    registry.register_handler("health_check", handle_health_check)

    logger.info(f"Registered {len(registry.get_registered_tools())} tools")


# Initialize middleware pipeline
def create_middleware_pipeline() -> MiddlewarePipeline:
    """Create the middleware pipeline for tool calls."""
    middlewares = [
        LoggingMiddleware(),
        ValidationMiddleware(),
        MetricsMiddleware(),
        RateLimiterMiddleware(),
    ]
    return MiddlewarePipeline(middlewares)


# Register tools and create middleware on module load
register_all_tools()
middleware_pipeline = create_middleware_pipeline()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    tools = []
    tools.extend(get_read_tools())
    tools.extend(get_edit_tools())
    tools.extend(get_slide_tools())
    tools.extend(get_notes_tools())
    tools.extend(get_text_replace_tools())
    tools.extend(get_health_tools())
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> dict:
    """Handle tool calls using registry and middleware pipeline."""
    logger.info(f"Tool call: {name} with arguments: {arguments}")

    try:
        # Get the tool registry
        registry = get_tool_registry()

        # Execute through middleware pipeline
        return await middleware_pipeline.execute(name, arguments, registry.dispatch)

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        raise


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    config = get_config()

    # Use configured search paths if available, otherwise use defaults
    if config.resource_search_paths:
        search_paths = config.resource_search_paths
    else:
        # Default search paths
        search_paths = [
            Path.cwd(),
            Path.cwd() / "src" / "deck",
            Path.cwd() / "src",
        ]

    resources = []
    for search_path in search_paths:
        if search_path.exists():
            resources.extend(list_pptx_resources(search_path))

    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read resource content."""
    logger.info(f"Reading resource: {uri}")

    try:
        resource_data = get_pptx_resource(uri)
        import json

        return json.dumps(resource_data, indent=2)
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
        raise


async def main():
    """Main entry point for MCP server."""
    logger.info("Starting PPTX MCP Server...")

    # Startup tasks
    try:
        config = get_config()
        logger.info(f"Running in {config.environment.value} environment")
        logger.info(f"Cache enabled: {config.performance.enable_cache}")
        logger.info(f"Rate limiting enabled: {config.performance.enable_rate_limiting}")

        # Initialize services if needed
        # (Cache and metrics are lazily initialized via ServiceRegistry)

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise

    try:
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )
    finally:
        # Shutdown tasks
        logger.info("Shutting down PPTX MCP Server...")
        try:
            # Perform any cleanup (cache persistence, etc.)
            # For now, just log
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
