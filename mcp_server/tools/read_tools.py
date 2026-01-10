"""Tools for reading PPTX content."""

from typing import Any, Dict

from mcp.types import Tool

from ..core.pptx_handler import PPTXHandler
from ..core.image_extractor import extract_slide_images


def get_read_tools() -> list[Tool]:
    """Get all read tools."""
    return [
        Tool(
            name="read_slide_content",
            description="Read comprehensive content from a slide including text, shapes, images, and visibility status",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number (1-indexed). If not provided, returns all slides.",  # noqa: E501
                        "minimum": 1,
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden slides in results (default: true). Only applicable when slide_number is not specified.",  # noqa: E501
                        "default": True,
                    },
                },
                "required": ["pptx_path"],
            },
        ),
        Tool(
            name="read_slide_text",
            description="Read all text content from a slide",
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number (1-indexed)",
                        "minimum": 1,
                    },
                },
                "required": ["pptx_path", "slide_number"],
            },
        ),
        Tool(
            name="read_slide_images",
            description="Read image information from a slide",
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number (1-indexed)",
                        "minimum": 1,
                    },
                },
                "required": ["pptx_path", "slide_number"],
            },
        ),
        Tool(
            name="read_presentation_info",
            description="Get presentation metadata including slide count, dimensions, and visibility statistics",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                },
                "required": ["pptx_path"],
            },
        ),
        Tool(
            name="read_slides_metadata",
            description="Get metadata for all slides including their visibility status (hidden/visible)",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "include_hidden": {
                        "type": "boolean",
                        "description": "Include hidden slides in results (default: true)",
                        "default": True,
                    },
                },
                "required": ["pptx_path"],
            },
        ),
    ]


async def handle_read_slide_content(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_slide_content tool call."""
    pptx_path = arguments["pptx_path"]
    slide_number = arguments.get("slide_number")
    include_hidden = arguments.get("include_hidden", True)

    handler = PPTXHandler(pptx_path)

    if slide_number:
        return handler.get_slide_content(slide_number)
    else:
        # Return all slides, optionally filtering hidden ones
        if include_hidden:
            # Include all slides without explicit hidden-checks here
            results = []
            for i in range(1, handler.get_slide_count() + 1):
                results.append(handler.get_slide_content(i))
        else:
            # Use metadata to determine visible slides and avoid duplicate hidden checks
            slides_metadata = handler.get_slides_metadata(include_hidden=False)
            results = []
            for meta in slides_metadata:
                slide_num = meta.get("slide_number")
                if slide_num is None:
                    continue
                results.append(handler.get_slide_content(slide_num))
        return {"slides": results}


async def handle_read_slide_text(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_slide_text tool call."""
    pptx_path = arguments["pptx_path"]
    slide_number = arguments["slide_number"]

    handler = PPTXHandler(pptx_path)
    text = handler.get_slide_text(slide_number)

    return {
        "slide_number": slide_number,
        "text": text,
    }


async def handle_read_slide_images(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_slide_images tool call."""
    pptx_path = arguments["pptx_path"]
    slide_number = arguments["slide_number"]

    images = extract_slide_images(pptx_path, slide_number)

    return {
        "slide_number": slide_number,
        "images": images,
    }


async def handle_read_presentation_info(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_presentation_info tool call."""
    pptx_path = arguments["pptx_path"]

    handler = PPTXHandler(pptx_path)
    return handler.get_presentation_info()


async def handle_read_slides_metadata(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_slides_metadata tool call."""
    pptx_path = arguments["pptx_path"]
    include_hidden = arguments.get("include_hidden", True)

    handler = PPTXHandler(pptx_path)
    slides = handler.get_slides_metadata(include_hidden=include_hidden)

    return {
        "pptx_path": pptx_path,
        "total_slides": handler.get_slide_count(),
        "slides": slides,
    }
