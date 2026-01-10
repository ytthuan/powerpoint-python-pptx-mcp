"""Main MCP server entry point."""

import asyncio
import logging
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool

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
from .resources.pptx_resources import list_pptx_resources, get_pptx_resource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create MCP server
server = Server("pptx-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    tools = []
    tools.extend(get_read_tools())
    tools.extend(get_edit_tools())
    tools.extend(get_slide_tools())
    tools.extend(get_notes_tools())
    tools.extend(get_text_replace_tools())
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> dict:
    """Handle tool calls."""
    logger.info(f"Tool call: {name} with arguments: {arguments}")

    try:
        # Read tools
        if name == "read_slide_content":
            return await handle_read_slide_content(arguments)
        elif name == "read_slide_text":
            return await handle_read_slide_text(arguments)
        elif name == "read_slide_images":
            return await handle_read_slide_images(arguments)
        elif name == "read_presentation_info":
            return await handle_read_presentation_info(arguments)
        elif name == "read_slides_metadata":
            return await handle_read_slides_metadata(arguments)

        # Edit tools
        elif name == "update_slide_text":
            return await handle_update_slide_text(arguments)
        elif name == "replace_slide_image":
            return await handle_replace_slide_image(arguments)
        elif name == "add_text_box":
            return await handle_add_text_box(arguments)
        elif name == "add_image":
            return await handle_add_image(arguments)
        elif name == "replace_slide_content":
            return await handle_replace_slide_content(arguments)
        elif name == "update_slide_content":
            return await handle_update_slide_content(arguments)

        # Slide management tools
        elif name == "add_slide":
            return await handle_add_slide(arguments)
        elif name == "delete_slide":
            return await handle_delete_slide(arguments)
        elif name == "duplicate_slide":
            return await handle_duplicate_slide(arguments)
        elif name == "change_slide_layout":
            return await handle_change_slide_layout(arguments)
        elif name == "set_slide_visibility":
            return await handle_set_slide_visibility(arguments)

        # Notes tools
        elif name == "read_notes":
            return await handle_read_notes(arguments)
        elif name == "read_notes_batch":
            return await handle_read_notes_batch(arguments)
        elif name == "update_notes":
            return await handle_update_notes(arguments)
        elif name == "update_notes_batch":
            return await handle_update_notes_batch(arguments)
        elif name == "format_notes_structure":
            return await handle_format_notes_structure(arguments)
        elif name == "process_notes_workflow":
            return await handle_process_notes_workflow(arguments)

        # Text replacement tools
        elif name == "replace_text":
            return await handle_replace_text(arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        raise


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List all available resources."""
    # Search in common locations
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

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
