"""Tools for transcribing embedded video audio in PPTX files."""

from __future__ import annotations

import json
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from mcp.types import Tool

from ..core.audio_extractor import extract_audio_from_video
from ..core.video_extractor import discover_embedded_videos
from ..exceptions import PPTXError, ValidationError, FileOperationError
from ..llm.audio_transcribe_client import transcribe_audio_file
from ..utils.async_utils import run_in_thread
from ..utils.validators import (
    parse_slide_range,
    validate_output_json_path,
    validate_pptx_path,
    validate_slide_numbers,
)

logger = logging.getLogger(__name__)


def get_transcript_tools() -> list[Tool]:
    """Return MCP tools for transcribing embedded video audio."""
    return [
        Tool(
            name="transcribe_embedded_video_audio",
            description=(
                "[Category: transcript] [Tags: video, audio, transcription] "
                "Transcribe audio from embedded videos within a PPTX file and write results to JSON."
            ),
            inputSchema={
                "type": "object",
                "anyOf": [{"required": ["slide_numbers"]}, {"required": ["slide_range"]}],
                "properties": {
                    "pptx_path": {"type": "string", "description": "Path to the PPTX file"},
                    "slide_numbers": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 1},
                        "description": "Slides to process (1-indexed)",
                    },
                    "slide_range": {
                        "type": "string",
                        "description": "Slide range (e.g., '1-5') used when slide_numbers is not provided",
                    },
                    "language": {
                        "type": "string",
                        "description": "Optional ISO-639-1 language hint for transcription",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Optional prompt to guide transcription",
                    },
                    "output_json_path": {
                        "type": "string",
                        "description": "Optional output JSON path; defaults to <pptx_path>.transcripts.json",
                    },
                    "include_raw_response": {
                        "type": "boolean",
                        "description": "Include raw Azure transcription response per audio segment",
                        "default": False,
                    },
                },
                "required": ["pptx_path"],
            },
        )
    ]


def _get_slide_count(pptx_path: Path) -> int:
    """Count slides in PPTX via zip contents."""
    try:
        with zipfile.ZipFile(pptx_path, "r") as zip_file:
            return len(
                [
                    name
                    for name in zip_file.namelist()
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                ]
            )
    except Exception as exc:
        raise FileOperationError(f"Unable to read PPTX slides: {exc}") from exc


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def handle_transcribe_embedded_video_audio(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Transcribe audio from embedded videos per slide."""
    pptx_path = validate_pptx_path(arguments["pptx_path"])

    slide_numbers_arg = arguments.get("slide_numbers")
    slide_range_arg = arguments.get("slide_range")
    requested_slides: List[int] = []

    if slide_numbers_arg is not None:
        if not isinstance(slide_numbers_arg, list):
            raise ValidationError("slide_numbers must be an array of integers")
        for value in slide_numbers_arg:
            if not isinstance(value, int):
                raise ValidationError("slide_numbers must contain only integers")
            requested_slides.append(value)

    if slide_range_arg:
        requested_slides.extend(parse_slide_range(slide_range_arg))

    if not requested_slides:
        raise ValidationError("Provide slide_numbers or slide_range to select slides for transcription")

    requested_slides = sorted(set(requested_slides))
    slide_count = _get_slide_count(pptx_path)
    validated_slides = validate_slide_numbers(requested_slides, slide_count)

    output_json_raw = arguments.get("output_json_path")
    if output_json_raw:
        output_json_path = validate_output_json_path(output_json_raw)
    else:
        output_json_path = validate_output_json_path(f"{pptx_path}.transcripts.json")

    language = arguments.get("language")
    prompt = arguments.get("prompt")
    include_raw = bool(arguments.get("include_raw_response", False))

    if language is not None and not isinstance(language, str):
        raise ValidationError("language must be a string when provided")
    if prompt is not None and not isinstance(prompt, str):
        raise ValidationError("prompt must be a string when provided")

    video_map = discover_embedded_videos(pptx_path, validated_slides)

    slides_output: List[Dict[str, Any]] = []
    total_videos = 0
    segments_transcribed = 0
    errors: List[str] = []

    with zipfile.ZipFile(pptx_path, "r") as zip_file, tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        for slide_number in validated_slides:
            slide_entry: Dict[str, Any] = {"slide_number": slide_number, "videos": []}
            videos = video_map.get(slide_number, [])

            if not videos:
                slide_entry["message"] = "No embedded video found for this slide"
                slides_output.append(slide_entry)
                continue

            for video_info in videos:
                video_result: Dict[str, Any] = {
                    "zip_path": video_info.get("zip_path"),
                    "filename": video_info.get("filename"),
                    "relationship_id": video_info.get("relationship_id"),
                    "size_bytes": video_info.get("size_bytes"),
                }

                try:
                    video_temp_path = temp_dir_path / f"{slide_number}_{video_info.get('relationship_id')}_{video_info.get('filename')}"
                    video_temp_path.parent.mkdir(parents=True, exist_ok=True)
                    video_temp_path.write_bytes(zip_file.read(video_info["zip_path"]))

                    audio_outputs = await run_in_thread(
                        extract_audio_from_video,
                        video_temp_path,
                        temp_dir_path / f"{video_temp_path.stem}.wav",
                    )

                    transcript_segments: List[Dict[str, Any]] = []
                    for segment_index, audio_path in enumerate(audio_outputs):
                        transcription = await run_in_thread(
                            transcribe_audio_file,
                            audio_path,
                            language=language,
                            prompt=prompt,
                            response_format="json",
                        )

                        segment_entry: Dict[str, Any] = {
                            "segment_index": segment_index,
                            "text": transcription.get("text"),
                        }
                        if include_raw:
                            segment_entry["raw_response"] = transcription

                        transcript_segments.append(segment_entry)
                        segments_transcribed += 1

                    video_result["transcripts"] = transcript_segments
                    total_videos += 1
                except PPTXError as exc:
                    error_message = str(exc)
                    video_result["error"] = error_message
                    errors.append(error_message)
                except Exception as exc:
                    error_message = (
                        f"Unexpected error processing embedded video {video_info.get('zip_path')}: {exc}"
                    )
                    video_result["error"] = error_message
                    errors.append(error_message)

                slide_entry["videos"].append(video_result)

            slides_output.append(slide_entry)

    summary = {
        "slides_requested": len(validated_slides),
        "slides_with_videos": len([s for s in slides_output if s.get("videos")]),
        "videos_processed": total_videos,
        "segments_transcribed": segments_transcribed,
        "error_count": len(errors),
    }

    result_payload = {
        "success": len(errors) == 0,
        "output_json_path": str(output_json_path),
        "slides": slides_output,
        "summary": summary,
        "errors": errors,
    }

    await run_in_thread(_write_json, output_json_path, result_payload)
    return result_payload
