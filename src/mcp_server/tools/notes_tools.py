"""Tools for speaker notes operations."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

from mcp.types import Tool

from ..core.pptx_handler import PPTXHandler
from ..core.safe_editor import update_notes_safe_in_place
from ..utils.async_utils import run_in_thread
from ..utils.validators import (
    parse_slide_range,
    validate_batch_updates,
    validate_pptx_path,
    validate_slide_number,
    validate_slide_numbers,
)


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
                        "description": "Slide number (1-indexed). If not provided, returns all slides.",  # noqa: E501
                        "minimum": 1,
                    },
                },
                "required": ["pptx_path"],
            },
        ),
        Tool(
            name="read_notes_batch",
            description="Read speaker notes from multiple slides at once for efficient batch processing",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "slide_numbers": {
                        "type": "array",
                        "description": "Array of slide numbers (1-indexed), e.g., [1, 5, 12, 20]",
                        "items": {
                            "type": "integer",
                            "minimum": 1,
                        },
                    },
                    "slide_range": {
                        "type": "string",
                        "description": "Slide range string like '1-10' (alternative to slide_numbers)",  # noqa: E501
                    },
                },
                "required": ["pptx_path"],
            },
        ),
        Tool(
            name="update_notes",
            description="Update speaker notes for a slide using safe zip-based editing (preserves animations/transitions)",  # noqa: E501
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
            name="update_notes_batch",
            description="Update speaker notes for multiple slides atomically using safe zip-based editing. All updates succeed or all fail (atomic operation).",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "updates": {
                        "type": "array",
                        "description": "Array of updates, each with slide_number and notes_text",
                        "items": {
                            "type": "object",
                            "properties": {
                                "slide_number": {
                                    "type": "integer",
                                    "description": "Slide number (1-indexed)",
                                    "minimum": 1,
                                },
                                "notes_text": {
                                    "type": "string",
                                    "description": "New notes text content",
                                },
                            },
                            "required": ["slide_number", "notes_text"],
                        },
                    },
                    "in_place": {
                        "type": "boolean",
                        "description": "Update file in-place (default: true for batch operations)",
                        "default": True,
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output PPTX path (optional, only used if in_place is false)",  # noqa: E501
                    },
                },
                "required": ["pptx_path", "updates"],
            },
        ),
        Tool(
            name="format_notes_structure",
            description="Format notes text into structured format (short/original template). Does NOT generate content, only formats structure.",  # noqa: E501
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
        Tool(
            name="process_notes_workflow",
            description="Orchestrate complete notes processing workflow: validate, format, and apply pre-processed notes to multiple slides atomically. AI agent provides already-processed content.",  # noqa: E501
            inputSchema={
                "type": "object",
                "properties": {
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to the PPTX file",
                    },
                    "notes_data": {
                        "type": "array",
                        "description": "Array of pre-processed notes with slide_number, short_text, and original_text",  # noqa: E501
                        "items": {
                            "type": "object",
                            "properties": {
                                "slide_number": {
                                    "type": "integer",
                                    "description": "Slide number (1-indexed)",
                                    "minimum": 1,
                                },
                                "short_text": {
                                    "type": "string",
                                    "description": "Short version text (AI-generated)",
                                },
                                "original_text": {
                                    "type": "string",
                                    "description": "Original/full version text (AI-generated)",
                                },
                            },
                            "required": ["slide_number", "short_text", "original_text"],
                        },
                    },
                    "in_place": {
                        "type": "boolean",
                        "description": "Update file in-place (default: true)",
                        "default": True,
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output PPTX path (optional, only used if in_place is false)",  # noqa: E501
                    },
                },
                "required": ["pptx_path", "notes_data"],
            },
        ),
    ]


async def handle_read_notes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_notes tool call."""
    pptx_path = arguments["pptx_path"]
    slide_number = arguments.get("slide_number")

    handler = PPTXHandler(pptx_path)
    return await handler.get_notes(slide_number)


async def handle_update_notes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update_notes tool call."""
    pptx_path = validate_pptx_path(arguments["pptx_path"])
    slide_number = arguments["slide_number"]
    notes_text = arguments["notes_text"]
    in_place = arguments.get("in_place", False)
    output_path = arguments.get("output_path")

    # Validate slide number
    handler = PPTXHandler(pptx_path)
    slide_count = await handler.get_slide_count()
    validate_slide_number(slide_number, slide_count)

    # Prepare updates
    updates = [(slide_number, notes_text)]

    if in_place:
        # Update in-place using safe zip-based editing
        await run_in_thread(update_notes_safe_in_place, pptx_path, updates)
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

            await run_in_thread(update_notes_safe, pptx_path, updates, output_path)
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


async def handle_read_notes_batch(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle read_notes_batch tool call."""
    try:
        pptx_path = validate_pptx_path(arguments["pptx_path"])
        slide_numbers = arguments.get("slide_numbers")
        slide_range = arguments.get("slide_range")

        # Validate that only one parameter is provided
        if slide_range and slide_numbers:
            raise ValueError(
                "Cannot specify both slide_range and slide_numbers. Please provide only one."
            )

        handler = PPTXHandler(pptx_path)
        max_slides = await handler.get_slide_count()

        # Determine which slides to read
        if slide_range:
            slide_numbers = parse_slide_range(slide_range)
            # Validate parsed range against max_slides
            slide_numbers = validate_slide_numbers(slide_numbers, max_slides)
        elif slide_numbers:
            slide_numbers = validate_slide_numbers(slide_numbers, max_slides)
        else:
            # If neither provided, return all slides
            slide_numbers = list(range(1, max_slides + 1))

        # Read notes for all specified slides
        results = []
        pres = await handler.get_presentation()
        for slide_num in slide_numbers:
            notes_text = ""
            slide = pres.slides[slide_num - 1]
            if slide.has_notes_slide:
                try:
                    notes_text = slide.notes_slide.notes_text_frame.text
                except Exception:
                    # If there's an issue reading notes text frame for this slide,
                    # leave notes_text as empty string and continue
                    pass

            results.append(
                {
                    "slide_number": slide_num,
                    "notes": notes_text,
                }
            )

        return {
            "success": True,
            "pptx_path": str(pptx_path),
            "total_slides": len(results),
            "slides": results,
        }
    except Exception as e:
        error_response: Dict[str, Any] = {
            "success": False,
            "error": str(e),
        }
        # Include context when available
        if "pptx_path" in locals():
            error_response["pptx_path"] = str(pptx_path)
        if "slide_numbers" in locals() and slide_numbers is not None:
            try:
                error_response["attempted_slides"] = len(slide_numbers)
            except TypeError:
                # slide_numbers might not be a sized iterable; ignore in that case
                pass
        return error_response


async def handle_update_notes_batch(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update_notes_batch tool call."""
    pptx_path = validate_pptx_path(arguments["pptx_path"])
    updates = arguments["updates"]
    in_place = arguments.get("in_place", True)
    output_path = arguments.get("output_path")

    # Validate updates
    handler = PPTXHandler(pptx_path)
    max_slides = await handler.get_slide_count()
    validated_updates = validate_batch_updates(updates, max_slides)

    # Prepare updates for safe_editor
    update_tuples = [(u["slide_number"], u["notes_text"]) for u in validated_updates]

    try:
        if in_place:
            # Update in-place using safe zip-based editing
            await run_in_thread(update_notes_safe_in_place, pptx_path, update_tuples)
            return {
                "success": True,
                "pptx_path": str(pptx_path),
                "updated_slides": len(validated_updates),
                "in_place": True,
                "slides": [u["slide_number"] for u in validated_updates],
            }
        else:
            # Create new file
            if not output_path:
                output_path = pptx_path.with_name(pptx_path.stem + ".notes.pptx")
            else:
                output_path = Path(output_path)

            from ..core.safe_editor import update_notes_safe

            await run_in_thread(update_notes_safe, pptx_path, update_tuples, output_path)

            return {
                "success": True,
                "output_path": str(output_path),
                "updated_slides": len(validated_updates),
                "in_place": False,
                "slides": [u["slide_number"] for u in validated_updates],
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "pptx_path": str(pptx_path),
            "attempted_slides": len(validated_updates),
        }


async def handle_process_notes_workflow(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle process_notes_workflow tool call.

    This tool orchestrates the complete workflow:
    1. Validate all inputs
    2. Format notes using short_original structure
    3. Apply all changes atomically
    """
    pptx_path = validate_pptx_path(arguments["pptx_path"])
    notes_data = arguments["notes_data"]
    in_place = arguments.get("in_place", True)
    output_path = arguments.get("output_path")

    # Validate notes_data structure
    if not notes_data or not isinstance(notes_data, list):
        return {
            "success": False,
            "error": "notes_data must be a non-empty list",
        }

    handler = PPTXHandler(pptx_path)
    max_slides = await handler.get_slide_count()

    # Validate and format all notes
    formatted_updates = []
    for i, note_data in enumerate(notes_data):
        if not isinstance(note_data, dict):
            return {
                "success": False,
                "error": f"Item at index {i} must be a dictionary",
            }

        slide_num = note_data.get("slide_number")
        short_text = note_data.get("short_text")
        original_text = note_data.get("original_text")

        if not isinstance(slide_num, int):
            return {
                "success": False,
                "error": f"Item at index {i}: slide_number must be integer",
            }

        if not isinstance(short_text, str) or not isinstance(original_text, str):
            return {
                "success": False,
                "error": f"Item at index {i}: short_text and original_text must be strings",
            }

        # Validate slide number
        try:
            validate_slide_number(slide_num, max_slides)
        except ValueError as e:
            return {
                "success": False,
                "error": f"Item at index {i}: {str(e)}",
            }

        # Format notes
        formatted_text = f"- Short version:\n{short_text}\n\n- Original:\n{original_text}"

        formatted_updates.append(
            {
                "slide_number": slide_num,
                "notes_text": formatted_text,
            }
        )

    # Apply all updates atomically
    result = await handle_update_notes_batch(
        {
            "pptx_path": str(pptx_path),
            "updates": formatted_updates,
            "in_place": in_place,
            "output_path": output_path,
        }
    )

    # Enhance result with workflow details
    if result.get("success"):
        result["workflow"] = "process_notes_workflow"
        result["formatted_slides"] = len(formatted_updates)

    return result
