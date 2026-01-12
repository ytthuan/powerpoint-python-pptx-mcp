"""MCP tools for Foundry-backed summarization, translation, and slide content generation."""

from __future__ import annotations

from typing import Any, Dict, Literal

from mcp.types import Tool

from ..core.pptx_handler import PPTXHandler
from ..exceptions import ValidationError
from ..llm.foundry_client import create_response
from ..llm.prompts import get_summarize_prompt, get_translate_prompt
from ..llm.slide_generate import generate_slide_content
from ..utils.validators import validate_text_input

SummarizeStyle = Literal["concise", "detailed", "bullet_points"]
OutputFormat = Literal["title+bullets", "speaker_notes", "json"]


def get_llm_tools() -> list[Tool]:
    """Get Foundry-backed LLM tools."""
    return [
        Tool(
            name="summarize_text_llm",
            description=(
                "[Category: llm] [Tags: summarize, text, notes] "
                "Summarize text using Azure AI Foundry (Models Responses API)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "style": {
                        "type": "string",
                        "enum": ["concise", "detailed", "bullet_points"],
                        "default": "concise",
                        "description": (
                            "Summary style: concise (brief), detailed (richer detail), "
                            "or bullet_points (bulleted list)"
                        ),
                    },
                    "max_words": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Optional maximum word count for the summary",
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 2,
                        "description": "Optional generation temperature (0-2)",
                    },
                    "max_output_tokens": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Optional maximum number of output tokens",
                    },
                },
                "required": ["text"],
            },
        ),
        Tool(
            name="translate_text_llm",
            description=(
                "[Category: llm] [Tags: translate, text, language] "
                "Translate text using Azure AI Foundry (Models Responses API)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "target_lang": {
                        "type": "string",
                        "description": "Target language (e.g., 'Vietnamese', 'English')",
                    },
                    "source_lang": {
                        "type": "string",
                        "description": "Optional source language (improves accuracy)",
                    },
                    "preserve_terms": {
                        "type": "array",
                        "description": "Optional list of terms that must stay unaltered",
                        "items": {"type": "string"},
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 2,
                        "description": "Optional generation temperature (0-2)",
                    },
                    "max_output_tokens": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Optional maximum number of output tokens",
                    },
                },
                "required": ["text", "target_lang"],
            },
        ),
        Tool(
            name="generate_slide_content_llm",
            description=(
                "[Category: llm] [Tags: slides, generation, notes] "
                "Generate slide content (title/bullets, speaker notes, or JSON) "
                "using slide metadata and Azure AI Foundry"
            ),
            inputSchema={
                "type": "object",
                "oneOf": [
                    {"required": ["slide_content"]},
                    {"required": ["pptx_path", "slide_number"]},
                ],
                "properties": {
                    "slide_content": {
                        "type": "object",
                        "description": "Slide metadata dictionary (if already available)",
                    },
                    "pptx_path": {
                        "type": "string",
                        "description": "Path to PPTX file (used when slide_content not provided)",
                    },
                    "slide_number": {
                        "type": "integer",
                        "minimum": 1,
                        "description": (
                            "Slide number to read (used when slide_content not provided)"
                        ),
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["title+bullets", "speaker_notes", "json"],
                        "default": "title+bullets",
                        "description": "Desired output format",
                    },
                    "language": {
                        "type": "string",
                        "default": "English",
                        "description": "Target language for generated content",
                    },
                    "temperature": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 2,
                        "description": "Optional generation temperature (0-2)",
                    },
                    "max_output_tokens": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Optional maximum number of output tokens",
                    },
                },
            },
        ),
    ]


async def handle_summarize_text(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize text using Foundry."""
    text = validate_text_input(arguments["text"])
    style: SummarizeStyle = _validate_summarize_style(arguments.get("style", "concise"))
    max_words = _validate_optional_positive_int(arguments.get("max_words"), "max_words")
    temperature = _validate_optional_temperature(arguments.get("temperature"))
    max_output_tokens = _validate_optional_positive_int(
        arguments.get("max_output_tokens"), "max_output_tokens"
    )

    prompt = get_summarize_prompt(text, style=style, max_words=max_words)
    summary = create_response(prompt, temperature=temperature, max_output_tokens=max_output_tokens)
    return {"summary": summary}


async def handle_translate_text(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Translate text using Foundry."""
    text = validate_text_input(arguments["text"])
    target_lang = _validate_language(arguments.get("target_lang"), field_name="target_lang")
    source_lang_raw = arguments.get("source_lang")
    source_lang = _validate_language(source_lang_raw, field_name="source_lang", allow_empty=True)
    preserve_terms = arguments.get("preserve_terms")
    temperature = _validate_optional_temperature(arguments.get("temperature"))
    max_output_tokens = _validate_optional_positive_int(
        arguments.get("max_output_tokens"), "max_output_tokens"
    )

    if preserve_terms is not None:
        if not isinstance(preserve_terms, list):
            raise ValidationError("preserve_terms must be a list of strings")
        for term in preserve_terms:
            if not isinstance(term, str):
                raise ValidationError("preserve_terms must contain only strings")

    prompt = get_translate_prompt(
        text,
        target_lang=target_lang,
        source_lang=source_lang,
        preserve_terms=preserve_terms,
    )
    translation = create_response(
        prompt, temperature=temperature, max_output_tokens=max_output_tokens
    )
    return {"translation": translation}


async def handle_generate_slide_content(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Generate slide content based on metadata or PPTX path."""
    slide_content = arguments.get("slide_content")
    pptx_path = arguments.get("pptx_path")
    slide_number = arguments.get("slide_number")
    output_format: OutputFormat = arguments.get("output_format", "title+bullets")
    language = arguments.get("language", "English")
    temperature = _validate_optional_temperature(arguments.get("temperature"))
    max_output_tokens = _validate_optional_positive_int(
        arguments.get("max_output_tokens"), "max_output_tokens"
    )

    if slide_content is None:
        if pptx_path is None or slide_number is None:
            raise ValidationError(
                "Either slide_content must be provided or both pptx_path and "
                "slide_number are required."
            )
        handler = PPTXHandler(pptx_path)
        slide_content = await handler.get_slide_content(slide_number)
    elif not isinstance(slide_content, dict):
        raise ValidationError("slide_content must be an object/dictionary")

    _validate_output_format(output_format)
    language_value = _validate_language(language, field_name="language")

    result = generate_slide_content(
        slide_content,
        output_format=output_format,
        language=language_value,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    return {"content": result, "format": output_format, "language": language_value}


def _validate_output_format(output_format: str) -> None:
    allowed: set[str] = {"title+bullets", "speaker_notes", "json"}
    if output_format not in allowed:
        raise ValidationError(f"output_format must be one of {sorted(allowed)}")


def _validate_summarize_style(style: Any) -> SummarizeStyle:
    allowed: set[str] = {"concise", "detailed", "bullet_points"}
    if style not in allowed:
        raise ValidationError(f"style must be one of {sorted(allowed)}")
    return style  # type: ignore[return-value]


def _validate_optional_positive_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValidationError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero")
    return value


def _validate_optional_temperature(value: Any) -> float | None:
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValidationError("temperature must be a number between 0 and 2")
    if value < 0 or value > 2:
        raise ValidationError("temperature must be between 0 and 2")
    return float(value)


def _validate_language(language: Any, *, field_name: str, allow_empty: bool = False) -> str | None:
    if language is None:
        if allow_empty:
            return None
        raise ValidationError(f"{field_name} is required")
    if not isinstance(language, str):
        raise ValidationError(f"{field_name} must be a string")
    if not language.strip():
        if allow_empty:
            return None
        raise ValidationError(f"{field_name} cannot be empty")
    return language.strip()
