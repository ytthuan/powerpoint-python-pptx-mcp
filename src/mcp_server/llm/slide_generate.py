"""Slide content generation helpers using Foundry-backed LLM."""

from __future__ import annotations

from typing import Literal

from .foundry_client import create_response
from .prompts import get_slide_generate_prompt


def normalize_slide_metadata(slide_content: dict) -> dict:
    """Normalize slide metadata coming from PPTXHandler.get_slide_content()."""
    normalized: dict = {}

    if "slide_number" in slide_content:
        normalized["slide_number"] = slide_content["slide_number"]
    elif "number" in slide_content:
        normalized["slide_number"] = slide_content["number"]

    if "title" in slide_content and slide_content["title"]:
        normalized["title"] = slide_content["title"]

    if "text" in slide_content and slide_content["text"]:
        normalized["text"] = slide_content["text"]

    shapes = slide_content.get("shapes", [])
    text_shapes: list[dict] = []
    images: list[dict] = []

    for shape in shapes:
        shape_type = shape.get("shape_type") or shape.get("type") or "unknown"
        shape_entry = {
            "type": shape_type,
            "text": shape.get("text", ""),
            "name": shape.get("name", ""),
        }

        if shape_entry["text"]:
            text_shapes.append(shape_entry)

        if shape.get("image"):
            image_info = {
                "alt_text": shape.get("name") or "Image",
            }
            if "image_path" in shape:
                image_info["source"] = shape["image_path"]
            images.append(image_info)

    if "text_shapes" in slide_content and not text_shapes:
        text_shapes = slide_content.get("text_shapes", [])

    normalized["text_shapes"] = text_shapes
    if images:
        normalized["images"] = images

    if "layout" in slide_content:
        normalized["layout"] = slide_content["layout"]
    if "visibility" in slide_content:
        normalized["visibility"] = slide_content["visibility"]
    elif "hidden" in slide_content:
        normalized["visibility"] = "hidden" if slide_content["hidden"] else "visible"

    return normalized


def generate_slide_content(
    slide_content: dict,
    *,
    output_format: Literal["title+bullets", "speaker_notes", "json"] = "title+bullets",
    language: str = "English",
    temperature: float | None = None,
    max_output_tokens: int | None = None,
) -> str:
    """Generate slide content from slide metadata."""
    normalized = normalize_slide_metadata(slide_content)
    prompt = get_slide_generate_prompt(normalized, output_format=output_format, language=language)
    return create_response(
        prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )
