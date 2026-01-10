"""Service layer interfaces and protocols for dependency injection.

This module defines Protocol classes (interfaces) for core services in the MCP server.
These protocols enable dependency injection and make the codebase more testable and maintainable.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class IPPTXHandler(Protocol):
    """Protocol for PPTX file operations handler."""
    
    @property
    def pptx_path(self) -> Path:
        """Get the PPTX file path."""
        ...
    
    def get_slide_count(self) -> int:
        """Get total number of slides in the presentation."""
        ...
    
    def is_slide_hidden(self, slide_number: int) -> bool:
        """Check if a slide is hidden.
        
        Args:
            slide_number: Slide number (1-indexed)
            
        Returns:
            True if slide is hidden, False if visible
        """
        ...
    
    def set_slide_hidden(self, slide_number: int, hidden: bool) -> None:
        """Set slide visibility.
        
        Args:
            slide_number: Slide number (1-indexed)
            hidden: True to hide, False to show
        """
        ...
    
    def get_presentation_info(self) -> Dict[str, Any]:
        """Get presentation metadata and information."""
        ...
    
    def get_slide_text(self, slide_number: int) -> str:
        """Get all text from a slide.
        
        Args:
            slide_number: Slide number (1-indexed)
            
        Returns:
            Combined text from all shapes on the slide
        """
        ...
    
    def get_slide_content(self, slide_number: int) -> Dict[str, Any]:
        """Get comprehensive slide content including text and shapes.
        
        Args:
            slide_number: Slide number (1-indexed)
            
        Returns:
            Dictionary with slide content details
        """
        ...
    
    def get_notes(self, slide_number: Optional[int] = None) -> Dict[str, Any]:
        """Get speaker notes from slide(s).
        
        Args:
            slide_number: Optional slide number. If None, returns all notes.
            
        Returns:
            Dictionary with notes information
        """
        ...
    
    def save(self, output_path: Optional[Path] = None) -> None:
        """Save the presentation.
        
        Args:
            output_path: Optional output path. If None, saves to original path.
        """
        ...


@runtime_checkable
class INotesEditor(Protocol):
    """Protocol for safe notes editing operations."""
    
    def update_notes(
        self,
        pptx_path: Path,
        slide_number: int,
        notes_text: str,
        output_path: Optional[Path] = None
    ) -> None:
        """Update notes for a single slide.
        
        Args:
            pptx_path: Path to PPTX file
            slide_number: Slide number (1-indexed)
            notes_text: New notes text
            output_path: Optional output path (None for in-place)
        """
        ...
    
    def update_notes_batch(
        self,
        pptx_path: Path,
        updates: List[Dict[str, Any]],
        output_path: Optional[Path] = None
    ) -> None:
        """Update notes for multiple slides.
        
        Args:
            pptx_path: Path to PPTX file
            updates: List of updates with slide_number and notes_text
            output_path: Optional output path (None for in-place)
        """
        ...


@runtime_checkable
class IValidator(Protocol):
    """Protocol for input validation operations."""
    
    def validate_pptx_path(self, path: str | Path) -> Path:
        """Validate and return Path object for PPTX file.
        
        Args:
            path: Path to validate
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If validation fails
        """
        ...
    
    def validate_slide_number(self, slide_number: int, max_slides: int) -> int:
        """Validate slide number is within range.
        
        Args:
            slide_number: Slide number to validate
            max_slides: Maximum number of slides
            
        Returns:
            Validated slide number
            
        Raises:
            ValidationError: If validation fails
        """
        ...
    
    def validate_text_input(
        self,
        text: str,
        max_length: Optional[int] = None
    ) -> str:
        """Validate text input.
        
        Args:
            text: Text to validate
            max_length: Optional maximum length
            
        Returns:
            Validated text
            
        Raises:
            ValidationError: If validation fails
        """
        ...


@runtime_checkable
class ICache(Protocol):
    """Protocol for caching operations."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        ...
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
        """
        ...
    
    def delete(self, key: str) -> None:
        """Delete value from cache.
        
        Args:
            key: Cache key
        """
        ...
    
    def clear(self) -> None:
        """Clear all cached values."""
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics (hits, misses, size, etc.)
        """
        ...


@runtime_checkable
class ILogger(Protocol):
    """Protocol for logging operations."""
    
    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message."""
        ...
    
    def info(self, msg: str, **kwargs) -> None:
        """Log info message."""
        ...
    
    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message."""
        ...
    
    def error(self, msg: str, **kwargs) -> None:
        """Log error message."""
        ...
    
    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message."""
        ...


@runtime_checkable
class IMetricsCollector(Protocol):
    """Protocol for metrics collection."""
    
    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        **kwargs
    ) -> None:
        """Record an operation metric.
        
        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            success: Whether operation succeeded
            **kwargs: Additional metric attributes
        """
        ...
    
    def increment_counter(self, metric: str, value: int = 1, **kwargs) -> None:
        """Increment a counter metric.
        
        Args:
            metric: Metric name
            value: Increment value
            **kwargs: Additional metric attributes
        """
        ...
    
    def record_gauge(self, metric: str, value: float, **kwargs) -> None:
        """Record a gauge metric.
        
        Args:
            metric: Metric name
            value: Gauge value
            **kwargs: Additional metric attributes
        """
        ...
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics.
        
        Returns:
            Dictionary of metrics
        """
        ...
