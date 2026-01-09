"""Input validation utilities for MCP server tools."""

from pathlib import Path
from typing import Any, List


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


def parse_slide_range(slide_range: str) -> List[int]:
    """Parse slide range string into list of slide numbers.
    
    Args:
        slide_range: Range string like "1-10" or "5-8"
        
    Returns:
        List of slide numbers in the range (inclusive)
        
    Raises:
        ValueError: If range format is invalid
    """
    if not slide_range or not isinstance(slide_range, str):
        raise ValueError(f"Invalid slide range: {slide_range!r}. Expected format: '1-10'")
    
    parts = slide_range.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid slide range format: {slide_range!r}. Expected format: '1-10'")
    
    try:
        start = int(parts[0].strip())
        end = int(parts[1].strip())
    except ValueError as e:
        raise ValueError(f"Invalid slide range numbers: {slide_range!r}. Both values must be integers.") from e
    
    if start < 1:
        raise ValueError(f"Slide range start must be >= 1, got {start}")
    if end < start:
        raise ValueError(f"Slide range end ({end}) must be >= start ({start})")
    
    return list(range(start, end + 1))


def validate_slide_numbers(slide_numbers: List[int], max_slides: int) -> List[int]:
    """Validate list of slide numbers are within valid range.
    
    Args:
        slide_numbers: List of slide numbers to validate
        max_slides: Maximum number of slides in presentation
        
    Returns:
        Validated list of slide numbers
        
    Raises:
        ValueError: If any slide number is invalid
    """
    if not slide_numbers:
        raise ValueError("Slide numbers list cannot be empty")
    
    if not isinstance(slide_numbers, list):
        raise ValueError(f"Slide numbers must be a list, got {type(slide_numbers).__name__}")
    
    validated = []
    for slide_num in slide_numbers:
        if not isinstance(slide_num, int):
            raise ValueError(f"All slide numbers must be integers, got {type(slide_num).__name__}: {slide_num!r}")
        validate_slide_number(slide_num, max_slides)
        validated.append(slide_num)
    
    return validated


def validate_batch_updates(updates: List[dict], max_slides: int) -> List[dict]:
    """Validate batch update structure.
    
    Args:
        updates: List of update dictionaries with slide_number and notes_text
        max_slides: Maximum number of slides in presentation
        
    Returns:
        Validated list of updates
        
    Raises:
        ValueError: If update structure is invalid
    """
    if not updates:
        raise ValueError("Updates list cannot be empty")
    
    if not isinstance(updates, list):
        raise ValueError(f"Updates must be a list, got {type(updates).__name__}")
    
    validated = []
    for i, update in enumerate(updates):
        if not isinstance(update, dict):
            raise ValueError(f"Update at index {i} must be a dictionary, got {type(update).__name__}")
        
        if "slide_number" not in update:
            raise ValueError(f"Update at index {i} missing required field 'slide_number'")
        
        if "notes_text" not in update:
            raise ValueError(f"Update at index {i} missing required field 'notes_text'")
        
        slide_num = update["slide_number"]
        notes_text = update["notes_text"]
        
        if not isinstance(slide_num, int):
            raise ValueError(f"Update at index {i}: slide_number must be integer, got {type(slide_num).__name__}")
        
        if not isinstance(notes_text, str):
            raise ValueError(f"Update at index {i}: notes_text must be string, got {type(notes_text).__name__}")
        
        validate_slide_number(slide_num, max_slides)
        validated.append(update)
    
    return validated


