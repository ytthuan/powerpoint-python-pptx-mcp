"""Input validation utilities for MCP server tools.

This module provides comprehensive input validation with security checks including:
- Path traversal prevention
- File size limits
- Workspace boundary enforcement
- Input sanitization
"""

import os
from pathlib import Path
from typing import Any, List, Optional

from ..config import get_config
from ..exceptions import (
    FileNotFoundError as PPTXFileNotFoundError,
    FileTooLargeError,
    InvalidPathError,
    InvalidSlideNumberError,
    PathTraversalError,
    ValidationError,
    WorkspaceBoundaryError,
    InputTooLargeError,
)


def _is_path_safe(path: Path) -> bool:
    """Check if path is safe (no path traversal).
    
    Args:
        path: Path to check
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve to absolute path
        resolved = path.resolve()
        
        # Check for path traversal patterns
        path_str = str(path)
        if ".." in path_str or path_str.startswith("/"):
            return False
        
        # Additional check: ensure resolved path doesn't escape
        # This catches cases like symlinks pointing outside
        return True
    except (OSError, RuntimeError):
        return False


def _check_workspace_boundary(path: Path) -> None:
    """Check if path is within workspace boundaries.
    
    Args:
        path: Path to check
        
    Raises:
        WorkspaceBoundaryError: If path is outside workspace boundaries
    """
    config = get_config()
    
    if not config.security.enforce_workspace_boundary:
        return
    
    if not config.security.workspace_dirs:
        # No workspace restrictions configured
        return
    
    resolved_path = path.resolve()
    
    # Check if path is within any allowed workspace directory
    for workspace_dir in config.security.workspace_dirs:
        try:
            resolved_path.relative_to(workspace_dir.resolve())
            return  # Path is within this workspace
        except ValueError:
            continue
    
    # Path is not within any workspace
    raise WorkspaceBoundaryError(
        str(resolved_path),
        [str(d) for d in config.security.workspace_dirs]
    )


def _check_file_size(path: Path) -> None:
    """Check if file size is within limits.
    
    Args:
        path: Path to file
        
    Raises:
        FileTooLargeError: If file exceeds size limit
    """
    config = get_config()
    
    if not path.exists():
        return  # Will be caught by other validation
    
    file_size = path.stat().st_size
    max_size = config.security.max_file_size
    
    if file_size > max_size:
        raise FileTooLargeError(
            str(path),
            file_size,
            max_size
        )


def validate_pptx_path(pptx_path: str | Path) -> Path:
    """Validate and return Path object for PPTX file.
    
    Performs comprehensive validation including:
    - File existence check
    - Extension validation
    - Path traversal prevention
    - Workspace boundary enforcement
    - File size limits
    
    Args:
        pptx_path: Path to PPTX file (string or Path object)
        
    Returns:
        Validated Path object
        
    Raises:
        PPTXFileNotFoundError: If file doesn't exist
        InvalidPathError: If path format is invalid
        PathTraversalError: If path traversal is detected
        WorkspaceBoundaryError: If path is outside workspace
        FileTooLargeError: If file exceeds size limit
    """
    # Convert to Path if string
    try:
        path = Path(pptx_path) if isinstance(pptx_path, str) else pptx_path
    except (TypeError, ValueError) as e:
        raise InvalidPathError(str(pptx_path), "Invalid path format") from e
    
    # Check path safety (prevent path traversal)
    if not _is_path_safe(path):
        raise PathTraversalError(str(path))
    
    # Check path length
    config = get_config()
    if len(str(path)) > config.security.max_path_length:
        raise InvalidPathError(
            str(path),
            f"Path too long (max: {config.security.max_path_length})"
        )
    
    # Check file exists
    if not path.exists():
        raise PPTXFileNotFoundError(str(path))
    
    # Check extension
    if path.suffix.lower() not in config.security.allowed_extensions:
        raise InvalidPathError(
            str(path),
            f"Invalid file extension. Allowed: {config.security.allowed_extensions}"
        )
    
    # Check workspace boundary
    _check_workspace_boundary(path)
    
    # Check file size
    _check_file_size(path)
    
    return path


def validate_slide_number(slide_number: int, max_slides: int) -> int:
    """Validate slide number is within valid range.
    
    Args:
        slide_number: Slide number to validate (1-indexed)
        max_slides: Maximum number of slides in presentation
        
    Returns:
        Validated slide number
        
    Raises:
        InvalidSlideNumberError: If slide number is invalid
    """
    if not isinstance(slide_number, int):
        raise ValidationError(
            f"Slide number must be an integer, got {type(slide_number).__name__}"
        )
    
    if slide_number < 1 or slide_number > max_slides:
        raise InvalidSlideNumberError(slide_number, max_slides)
    
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
    """Validate and return Path object for image file.
    
    Performs validation including:
    - File existence check
    - Extension validation
    - Path safety checks
    - Workspace boundary enforcement
    - File size limits
    
    Args:
        image_path: Path to image file
        
    Returns:
        Validated Path object
        
    Raises:
        PPTXFileNotFoundError: If file doesn't exist
        InvalidPathError: If path or extension is invalid
        PathTraversalError: If path traversal detected
        WorkspaceBoundaryError: If path outside workspace
        FileTooLargeError: If file too large
    """
    # Convert to Path
    try:
        path = Path(image_path) if isinstance(image_path, str) else image_path
    except (TypeError, ValueError) as e:
        raise InvalidPathError(str(image_path), "Invalid path format") from e
    
    # Check path safety
    if not _is_path_safe(path):
        raise PathTraversalError(str(path))
    
    # Check path length
    config = get_config()
    if len(str(path)) > config.security.max_path_length:
        raise InvalidPathError(
            str(path),
            f"Path too long (max: {config.security.max_path_length})"
        )
    
    # Check file exists
    if not path.exists():
        raise PPTXFileNotFoundError(str(path))
    
    # Validate extension
    valid_extensions = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
    if path.suffix.lower() not in valid_extensions:
        raise InvalidPathError(
            str(path),
            f"Unsupported image format: {path.suffix}. Supported: {valid_extensions}"
        )
    
    # Check workspace boundary
    _check_workspace_boundary(path)
    
    # Check file size
    _check_file_size(path)
    
    return path


def validate_text_input(text: str, max_length: Optional[int] = None) -> str:
    """Validate text input with length limits.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length (uses config default if None)
        
    Returns:
        Validated text
        
    Raises:
        ValidationError: If text is invalid
        InputTooLargeError: If text exceeds length limit
    """
    if not isinstance(text, str):
        raise ValidationError(
            f"Text must be a string, got {type(text).__name__}"
        )
    
    if max_length is None:
        config = get_config()
        max_length = config.security.max_text_length
    
    text_length = len(text)
    if text_length > max_length:
        raise InputTooLargeError("text", text_length, max_length)
    
    return text


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


