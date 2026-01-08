"""Input validation utilities for MCP server tools."""

from pathlib import Path
from typing import Any


def validate_pptx_path(pptx_path: str | Path) -> Path:
    """Validate and return Path object for PPTX file."""
    path = Path(pptx_path) if isinstance(pptx_path, str) else pptx_path
    if not path.exists():
        raise ValueError(f"PPTX file not found: {path}")
    if not path.suffix.lower() == ".pptx":
        raise ValueError(f"File is not a PPTX file: {path}")
    return path


def validate_slide_number(slide_number: int, max_slides: int) -> int:
    """Validate slide number is within valid range."""
    if slide_number < 1:
        raise ValueError(f"Slide number must be >= 1, got {slide_number}")
    if slide_number > max_slides:
        raise ValueError(f"Slide number {slide_number} exceeds total slides ({max_slides})")
    return slide_number


def validate_position(position: dict[str, Any] | None) -> dict[str, float]:
    """Validate position dictionary with x, y coordinates."""
    if position is None:
        return {"x": 0.0, "y": 0.0}
    if not isinstance(position, dict):
        raise ValueError("Position must be a dictionary")
    x = position.get("x", 0.0)
    y = position.get("y", 0.0)
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        raise ValueError("Position x and y must be numbers")
    return {"x": float(x), "y": float(y)}


def validate_size(size: dict[str, Any] | None) -> dict[str, float]:
    """Validate size dictionary with width, height."""
    if size is None:
        return {"width": 100.0, "height": 100.0}
    if not isinstance(size, dict):
        raise ValueError("Size must be a dictionary")
    width = size.get("width", 100.0)
    height = size.get("height", 100.0)
    if not isinstance(width, (int, float)) or not isinstance(height, (int, float)):
        raise ValueError("Size width and height must be numbers")
    if width <= 0 or height <= 0:
        raise ValueError("Size width and height must be positive")
    return {"width": float(width), "height": float(height)}


def validate_image_path(image_path: str | Path) -> Path:
    """Validate and return Path object for image file."""
    path = Path(image_path) if isinstance(image_path, str) else image_path
    if not path.exists():
        raise ValueError(f"Image file not found: {path}")
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    if path.suffix.lower() not in valid_extensions:
        raise ValueError(f"Unsupported image format: {path.suffix}. Supported: {valid_extensions}")
    return path


