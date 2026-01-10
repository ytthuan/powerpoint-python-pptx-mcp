"""Custom exception hierarchy for MCP server.

This module defines a structured exception hierarchy for better error handling,
categorization, and recovery strategies throughout the MCP server.
"""

from typing import Any, Optional


class PPTXError(Exception):
    """Base exception for all PPTX MCP server errors.
    
    All custom exceptions should inherit from this base class.
    This allows for catching all server-specific errors with a single except clause.
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """Initialize PPTXError.
        
        Args:
            message: Human-readable error message
            details: Additional error details (for structured logging)
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the error
        """
        result = {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }
        if self.cause:
            result["cause"] = str(self.cause)
        return result


# ============================================================================
# Validation Errors
# ============================================================================

class ValidationError(PPTXError):
    """Raised when input validation fails.
    
    This includes invalid parameters, malformed data, or constraint violations.
    """
    pass


class InvalidSlideNumberError(ValidationError):
    """Raised when a slide number is out of valid range."""
    
    def __init__(self, slide_number: int, max_slides: int, **kwargs):
        super().__init__(
            f"Invalid slide number: {slide_number}. Must be between 1 and {max_slides}",
            details={"slide_number": slide_number, "max_slides": max_slides},
            **kwargs
        )


class InvalidPathError(ValidationError):
    """Raised when a file path is invalid or insecure."""
    
    def __init__(self, path: str, reason: str = "Invalid path", **kwargs):
        super().__init__(
            f"{reason}: {path}",
            details={"path": path, "reason": reason},
            **kwargs
        )


class InvalidFormatError(ValidationError):
    """Raised when data format is invalid."""
    
    def __init__(self, format_name: str, expected: str, got: str, **kwargs):
        super().__init__(
            f"Invalid {format_name} format. Expected: {expected}, got: {got}",
            details={"format": format_name, "expected": expected, "got": got},
            **kwargs
        )


class InputTooLargeError(ValidationError):
    """Raised when input exceeds size limits."""
    
    def __init__(self, input_type: str, size: int, max_size: int, **kwargs):
        super().__init__(
            f"{input_type} size ({size} bytes) exceeds maximum allowed ({max_size} bytes)",
            details={"input_type": input_type, "size": size, "max_size": max_size},
            **kwargs
        )


# ============================================================================
# File Operation Errors
# ============================================================================

class FileOperationError(PPTXError):
    """Base class for file operation errors."""
    pass


class PPTXFileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""
    
    def __init__(self, file_path: str, **kwargs):
        super().__init__(
            f"File not found: {file_path}",
            details={"file_path": file_path},
            **kwargs
        )


class FileAccessError(FileOperationError):
    """Raised when file access is denied or restricted."""
    
    def __init__(self, file_path: str, reason: str = "Access denied", **kwargs):
        super().__init__(
            f"Cannot access file: {file_path}. Reason: {reason}",
            details={"file_path": file_path, "reason": reason},
            **kwargs
        )


class FileCorruptedError(FileOperationError):
    """Raised when a file is corrupted or invalid."""
    
    def __init__(self, file_path: str, reason: str = "File corrupted", **kwargs):
        super().__init__(
            f"File is corrupted or invalid: {file_path}. Reason: {reason}",
            details={"file_path": file_path, "reason": reason},
            **kwargs
        )


class FileTooLargeError(FileOperationError):
    """Raised when a file exceeds size limits."""
    
    def __init__(self, file_path: str, size: int, max_size: int, **kwargs):
        super().__init__(
            f"File too large: {file_path} ({size} bytes). Maximum allowed: {max_size} bytes",
            details={"file_path": file_path, "size": size, "max_size": max_size},
            **kwargs
        )


# ============================================================================
# Presentation Errors
# ============================================================================

class PresentationError(PPTXError):
    """Base class for presentation-related errors."""
    pass


class SlideNotFoundError(PresentationError):
    """Raised when a requested slide is not found."""
    
    def __init__(self, slide_number: int, **kwargs):
        super().__init__(
            f"Slide not found: {slide_number}",
            details={"slide_number": slide_number},
            **kwargs
        )


class LayoutNotFoundError(PresentationError):
    """Raised when a requested slide layout is not found."""
    
    def __init__(self, layout_name: str, **kwargs):
        super().__init__(
            f"Layout not found: {layout_name}",
            details={"layout_name": layout_name},
            **kwargs
        )


class ShapeNotFoundError(PresentationError):
    """Raised when a requested shape is not found."""
    
    def __init__(self, shape_id: Any, slide_number: int, **kwargs):
        super().__init__(
            f"Shape not found: {shape_id} on slide {slide_number}",
            details={"shape_id": shape_id, "slide_number": slide_number},
            **kwargs
        )


class NotesNotFoundError(PresentationError):
    """Raised when speaker notes are not found."""
    
    def __init__(self, slide_number: int, **kwargs):
        super().__init__(
            f"Notes not found for slide {slide_number}",
            details={"slide_number": slide_number},
            **kwargs
        )


# ============================================================================
# Security Errors
# ============================================================================

class SecurityError(PPTXError):
    """Base class for security-related errors."""
    pass


class PathTraversalError(SecurityError):
    """Raised when a path traversal attack is detected."""
    
    def __init__(self, path: str, **kwargs):
        super().__init__(
            f"Path traversal detected: {path}",
            details={"path": path},
            **kwargs
        )


class WorkspaceBoundaryError(SecurityError):
    """Raised when file access violates workspace boundaries."""
    
    def __init__(self, path: str, allowed_dirs: list[str], **kwargs):
        super().__init__(
            f"File access outside workspace boundary: {path}",
            details={"path": path, "allowed_dirs": allowed_dirs},
            **kwargs
        )


class UnsafeOperationError(SecurityError):
    """Raised when an operation is deemed unsafe."""
    
    def __init__(self, operation: str, reason: str, **kwargs):
        super().__init__(
            f"Unsafe operation: {operation}. Reason: {reason}",
            details={"operation": operation, "reason": reason},
            **kwargs
        )


# ============================================================================
# Resource Errors
# ============================================================================

class ResourceError(PPTXError):
    """Base class for resource management errors."""
    pass


class ResourceExhaustedError(ResourceError):
    """Raised when resources are exhausted (memory, cache, etc.)."""
    
    def __init__(self, resource_type: str, **kwargs):
        super().__init__(
            f"Resource exhausted: {resource_type}",
            details={"resource_type": resource_type},
            **kwargs
        )


class OperationTimeoutError(ResourceError):
    """Raised when an operation times out."""
    
    def __init__(self, operation: str, timeout: int, **kwargs):
        super().__init__(
            f"Operation timed out: {operation} (timeout: {timeout}s)",
            details={"operation": operation, "timeout": timeout},
            **kwargs
        )


class RateLimitExceededError(ResourceError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window: str, **kwargs):
        super().__init__(
            f"Rate limit exceeded: {limit} requests per {window}",
            details={"limit": limit, "window": window},
            **kwargs
        )


# ============================================================================
# Integration Errors
# ============================================================================

class IntegrationError(PPTXError):
    """Base class for external integration errors."""
    pass


class AzureAPIError(IntegrationError):
    """Raised when Azure API calls fail."""
    
    def __init__(self, operation: str, status_code: Optional[int] = None, **kwargs):
        super().__init__(
            f"Azure API error during {operation}" + 
            (f" (status: {status_code})" if status_code else ""),
            details={"operation": operation, "status_code": status_code},
            **kwargs
        )


# ============================================================================
# Cache Errors
# ============================================================================

class CacheError(PPTXError):
    """Base class for cache-related errors."""
    pass


class CacheMissError(CacheError):
    """Raised when a cache lookup fails."""
    
    def __init__(self, key: str, **kwargs):
        super().__init__(
            f"Cache miss for key: {key}",
            details={"key": key},
            **kwargs
        )


class CacheInvalidationError(CacheError):
    """Raised when cache invalidation fails."""
    
    def __init__(self, key: str, reason: str, **kwargs):
        super().__init__(
            f"Cache invalidation failed for key: {key}. Reason: {reason}",
            details={"key": key, "reason": reason},
            **kwargs
        )
