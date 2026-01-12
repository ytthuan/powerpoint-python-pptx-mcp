"""Prompt templates for Foundry-backed summarization, translation, and slide content generation."""

from __future__ import annotations

from typing import Literal, Optional


def get_summarize_prompt(
    text: str,
    *,
    style: Literal["concise", "detailed", "bullet_points"] = "concise",
    max_words: Optional[int] = None,
) -> str:
    """Build a prompt for text summarization."""
    style_instructions = {
        "concise": "Provide a brief, concise summary focusing on the main points.",
        "detailed": "Provide a comprehensive summary with key details and context.",
        "bullet_points": "Provide a summary in bullet point format, highlighting key points.",
    }

    style_instruction = style_instructions.get(style, style_instructions["concise"])
    word_limit = (
        f" The summary should be approximately {max_words} words or less." if max_words else ""
    )

    return (
        f"Summarize the following text.{word_limit}\n\n"
        f"{style_instruction}\n\n"
        f"Text to summarize:\n{text}\n\n"
        "Summary:"
    )


def get_translate_prompt(
    text: str,
    *,
    target_lang: str,
    source_lang: Optional[str] = None,
    preserve_terms: Optional[list[str]] = None,
) -> str:
    """Build a prompt for text translation with tone guidance."""
    source_info = f" from {source_lang}" if source_lang else ""
    preserve_info = ""
    if preserve_terms:
        terms_list = ", ".join(f'"{term}"' for term in preserve_terms)
        preserve_info = f"\n\nIMPORTANT: Preserve these terms exactly as written (do not translate): {terms_list}"

    return (
        f"Translate the following text{source_info} to {target_lang}.{preserve_info}\n\n"
        "Maintain the original meaning, tone, and style. If the text contains technical terms or proper nouns, keep them in their original form unless they have a standard translation.\n\n"
        f"Text to translate:\n{text}\n\n"
        "Translation:"
    )


def get_slide_generate_prompt(
    slide_content: dict,
    *,
    output_format: Literal["title+bullets", "speaker_notes", "json"] = "title+bullets",
    language: str = "English",
) -> str:
    """Build a prompt for generating slide content from slide metadata."""
    format_instructions = {
        "title+bullets": (
            "Generate a slide title and bullet points based on the provided metadata. "
            "Format: Title on first line, followed by bullet points (one per line, prefixed with '- ').\n\n"
            "TONE AND STYLE GUIDELINES:\n"
            "- Use clear, concise language suitable for presentation slides\n"
            "- Keep bullet points brief and scannable (one key idea per bullet)\n"
            "- Use professional but accessible tone\n"
            "- Avoid long paragraphs; prefer short, impactful statements\n"
            "- Ensure content is presentation-ready and visually digestible"
        ),
        "speaker_notes": (
            "Generate speaker notes based on the provided slide metadata. "
            "Create conversational, speakable notes suitable for a live presentation.\n\n"
            "TONE AND STYLE GUIDELINES:\n"
            "- Use conversational, casual tone suitable for live presentation\n"
            "- Keep sentences short and speakable (easy to read aloud)\n"
            "- Use simple bullet points; avoid long paragraphs unless necessary\n"
            "- Make content engaging and natural-sounding when spoken\n"
            "- For Vietnamese: Address audience as 'anh/chị' (never 'bạn' or 'quý vị')\n"
            "- For Vietnamese: Use 'chúng ta' for shared actions/goals\n"
            "- Do NOT invent facts, product claims, or numbers\n"
            "- If citing statistics, include source attribution (e.g., 'Nguồn: ...')\n"
            "- Do NOT write transition phrases referencing the next slide\n"
            "- End with a neutral wrap-up that stands alone\n"
            "- Focus on what the presenter should say, not what's already on the slide"
        ),
        "json": (
            "Generate structured slide content in JSON format with 'title' and 'content' fields. "
            "The content field should contain an array of bullet points or paragraphs.\n\n"
            "TONE AND STYLE GUIDELINES:\n"
            "- Use clear, concise language suitable for presentation\n"
            "- Maintain professional but accessible tone\n"
            "- Keep content presentation-ready and well-structured"
        ),
    }

    format_instruction = format_instructions.get(
        output_format, format_instructions["title+bullets"]
    )
    language_tone = _get_language_tone_instructions(language, output_format)
    metadata_str = _format_slide_metadata(slide_content)

    return (
        f"Generate slide content in {language} based on the following slide metadata.\n\n"
        f"{format_instruction}\n\n"
        f"{language_tone}\n\n"
        "CRITICAL RULES:\n"
        "- Use ONLY the information provided in the metadata below\n"
        "- Do NOT invent images, text, or content that is not present in the metadata\n"
        "- If a field is empty or missing, do not create content for it\n"
        "- Maintain accuracy and avoid adding fictional details\n\n"
        f"Slide Metadata:\n{metadata_str}\n\n"
        "Generated Content:"
    )


def _get_language_tone_instructions(language: str, output_format: str) -> str:
    """Language-specific tone guidelines, especially for speaker notes."""
    language_lower = language.lower()

    if "vietnamese" in language_lower or "tiếng việt" in language_lower:
        if output_format == "speaker_notes":
            return (
                "VIETNAMESE-SPECIFIC TONE REQUIREMENTS:\n"
                "- Pronouns: Always address audience as 'anh/chị' (never use 'bạn' or 'quý vị')\n"
                "- Collective: Use 'chúng ta' for shared actions/goals\n"
                "- Tone: Conversational, casual, suitable for live presentation\n"
                "- Sentences: Keep short and speakable\n"
                "- Format: Simple bullet points; avoid long paragraphs\n"
                "- Technical terms: Do NOT translate technical terms (keep them in original form)\n"
                "- Facts: Do NOT invent product claims or numbers\n"
                "- Transitions: Do NOT write transition phrases referencing the next slide"
            )
        return (
            "VIETNAMESE-SPECIFIC REQUIREMENTS:\n"
            "- Use clear, natural Vietnamese\n"
            "- Keep technical terms in original form (do not translate)\n"
            "- Maintain professional but accessible tone"
        )

    if "english" in language_lower or language_lower == "en":
        if output_format == "speaker_notes":
            return (
                "ENGLISH TONE REQUIREMENTS:\n"
                "- Use conversational, engaging tone suitable for live presentation\n"
                "- Address audience naturally (e.g., 'you', 'we', 'let's')\n"
                "- Keep sentences short and speakable\n"
                "- Use simple bullet points; avoid long paragraphs"
            )
        return (
            "ENGLISH TONE REQUIREMENTS:\n"
            "- Use clear, professional English\n"
            "- Maintain accessible, engaging tone"
        )

    if output_format == "speaker_notes":
        return (
            f"TONE REQUIREMENTS FOR {language.upper()}:\n"
            "- Use conversational, engaging tone suitable for live presentation\n"
            "- Keep sentences short and speakable\n"
            "- Use simple bullet points; avoid long paragraphs\n"
            "- Address audience naturally and appropriately for the language"
        )

    return (
        f"TONE REQUIREMENTS FOR {language.upper()}:\n"
        "- Use clear, natural language\n"
        "- Maintain professional but accessible tone"
    )


def _format_slide_metadata(slide_content: dict) -> str:
    """Format slide metadata dictionary into a readable string."""
    lines: list[str] = []

    slide_number = slide_content.get("slide_number")
    if slide_number is not None:
        lines.append(f"Slide Number: {slide_number}")

    title = slide_content.get("title") or ""
    if title:
        lines.append(f"Title: {title}")

    text_content = slide_content.get("text")
    if text_content:
        lines.append("\nSlide Text:")
        lines.append(text_content)

    shapes = slide_content.get("shapes", [])
    text_shapes = slide_content.get("text_shapes", [])
    combined_shapes = text_shapes or shapes
    if combined_shapes:
        lines.append("\nShapes:")
        for idx, shape in enumerate(combined_shapes, start=1):
            shape_type = shape.get("shape_type") or shape.get("type") or "unknown"
            shape_text = shape.get("text") or ""
            name = shape.get("name") or ""
            prefix = f"  {idx}. [{shape_type}]"
            if name:
                prefix = f"{prefix} {name}"
            if shape_text:
                lines.append(f"{prefix}: {shape_text}")
            elif shape.get("image"):
                lines.append(f"{prefix}: <image>")
            else:
                lines.append(prefix)

    if slide_content.get("hidden") is not None:
        visibility = "hidden" if slide_content.get("hidden") else "visible"
        lines.append(f"\nVisibility: {visibility}")

    return "\n".join(lines) if lines else "No metadata available"
