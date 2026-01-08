"""Tools for speaker notes operations."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from mcp.types import Tool

from ..core.pptx_handler import PPTXHandler
from ..core.safe_editor import update_notes_safe_in_place, _iter_updates
from ..utils.validators import validate_pptx_path, validate_slide_number


def get_notes_tools() -> list[Tool]:
    """Get all notes tools."""
    return [
        Tool(
            name="read_notes",
            description="Read speaker notes from slide(s)",
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "slide_number": {
                        "type": "integer",
                        "description": "Slide number (1-indexed). If not provided, returns all slides.",
                        "minimum": 1,
                    },
                },
                "required": ["pptx_path"],
            },
        ),
        Tool(
            name="update_notes",
            description="Update speaker notes for a slide using safe zip-based editing (preserves animations/transitions)",
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
                    "notes_text": {
                        "type": "string",
                        "description": "New notes text content",
                    },
                    "in_place": {
                        "type": "boolean",
                        "description": "Update file in-place (default: false, creates new file)",
                        "default": False,
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output PPTX path (required if in_place is false)",
                    },
                },
                "required": ["pptx_path", "slide_number", "notes_text"],
            },
        ),
        Tool(
            name="format_notes_structure",
            description="Format notes text into structured format (short/original template). Does NOT generate content, only formats structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "short_text": {
                        "type": "string",
                        "description": "Short version text",
                    },
                    "original_text": {
                        "type": "string",
                        "description": "Original/full version text",
                    },
                    "format_type": {
                        "type": "string",
                        "description": "Format type: 'short_original' (default) or 'simple'",
                        "enum": ["short_original", "simple"],
                        "default": "short_original",
                    },
                },
                "required": ["short_text", "original_text"],
            },
        ),
    ]


async def handle_read_notes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_notes tool call."""
    pptx_path = arguments["pptx_path"]
    slide_number = arguments.get("slide_number")
    
    handler = PPTXHandler(pptx_path)
    return handler.get_notes(slide_number)


async def handle_update_notes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update_notes tool call."""
    pptx_path = validate_pptx_path(arguments["pptx_path"])
    slide_number = arguments["slide_number"]
    notes_text = arguments["notes_text"]
    in_place = arguments.get("in_place", False)
    output_path = arguments.get("output_path")
    
    # Validate slide number
    handler = PPTXHandler(pptx_path)
    validate_slide_number(slide_number, handler.get_slide_count())
    
    # Prepare updates
    updates = [(slide_number, notes_text)]
    
    if in_place:
        # Update in-place using safe zip-based editing
        update_notes_safe_in_place(pptx_path, updates)
        return {
            "success": True,
            "pptx_path": str(pptx_path),
            "slide_number": slide_number,
            "in_place": True,
        }
    else:
        # Create new file
        if not output_path:
            output_path = pptx_path.with_name(pptx_path.stem + ".notes.pptx")
        else:
            output_path = Path(output_path)
        
        # Create temporary JSON file for updates
        updates_json = {
            "slides": [
                {
                    "slide": slide_number,
                    "notes": notes_text,
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_file:
            json.dump(updates_json, tmp_file, ensure_ascii=False)
            tmp_path = Path(tmp_file.name)
        
        try:
            from ..core.safe_editor import update_notes_safe
            update_notes_safe(pptx_path, updates, output_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
        
        return {
            "success": True,
            "output_path": str(output_path),
            "slide_number": slide_number,
            "in_place": False,
        }


async def handle_format_notes_structure(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle format_notes_structure tool call."""
    short_text = arguments["short_text"]
    original_text = arguments["original_text"]
    format_type = arguments.get("format_type", "short_original")
    
    if format_type == "short_original":
        formatted = f"- Short version:\n{short_text}\n\n- Original:\n{original_text}"
    else:  # simple
        formatted = f"{short_text}\n\n{original_text}"
    
    return {
        "formatted_text": formatted,
        "format_type": format_type,
    }


