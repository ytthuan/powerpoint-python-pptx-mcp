"""Structured logging with correlation IDs for request tracing.

This module provides enhanced logging capabilities including:
- Correlation IDs for request tracing
- Structured logging (JSON format)
- Context-aware logging
- Sensitive data masking
- Log sampling for high-volume operations
"""

import contextvars
import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Any, Optional

from .config import get_config


# Context variable for correlation ID
correlation_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'correlation_id', default=None
)


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record.
        
        Args:
            record: Log record to modify
            
        Returns:
            True to allow record to be logged
        """
        correlation_id = correlation_id_var.get()
        record.correlation_id = correlation_id if correlation_id else "no-correlation-id"
        return True


class StructuredFormatter(logging.Formatter):
    """Formatter that outputs logs in structured JSON format."""
    
    def __init__(self, mask_sensitive: bool = True):
        """Initialize structured formatter.
        
        Args:
            mask_sensitive: Whether to mask sensitive data in logs
        """
        super().__init__()
        self.mask_sensitive = mask_sensitive
        self.sensitive_keys = {"password", "token", "secret", "api_key", "credential"}
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": getattr(record, "correlation_id", "no-correlation-id"),
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra_fields"):
            extra = record.extra_fields
            if self.mask_sensitive:
                extra = self._mask_sensitive_data(extra)
            log_data["extra"] = extra
        
        # Add location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        return json.dumps(log_data)
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Mask sensitive data in log output.
        
        Args:
            data: Data to mask
            
        Returns:
            Masked data
        """
        if isinstance(data, dict):
            return {
                key: "***MASKED***" if any(s in key.lower() for s in self.sensitive_keys)
                else self._mask_sensitive_data(value)
                for key, value in data.items()
            }
        elif isinstance(data, (list, tuple)):
            return [self._mask_sensitive_data(item) for item in data]
        return data


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds structured logging support."""
    
    def process(self, msg: str, kwargs: dict) -> tuple[str, dict]:
        """Process log message and add extra fields.
        
        Args:
            msg: Log message
            kwargs: Keyword arguments
            
        Returns:
            Tuple of (message, modified kwargs)
        """
        # Extract extra fields
        extra = kwargs.get("extra", {})
        
        # Add correlation ID
        correlation_id = correlation_id_var.get()
        if correlation_id:
            extra["correlation_id"] = correlation_id
        
        # Store extra fields in a way that our formatter can access
        if "extra_fields" not in extra:
            extra["extra_fields"] = {}
        
        # Move all non-standard fields to extra_fields
        for key in list(kwargs.keys()):
            if key not in {"extra", "exc_info", "stack_info", "stacklevel"}:
                extra["extra_fields"][key] = kwargs.pop(key)
        
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """Setup logging configuration based on config.
    
    This should be called once at application startup.
    """
    config = get_config()
    log_config = config.logging
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config.level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_config.level)
    
    # Use structured formatter if enabled
    if log_config.enable_structured_logging:
        formatter = StructuredFormatter(mask_sensitive=not log_config.log_sensitive_data)
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s"
        )
    
    console_handler.setFormatter(formatter)
    
    # Add correlation ID filter
    if log_config.enable_correlation_ids:
        console_handler.addFilter(CorrelationIdFilter())
    
    root_logger.addHandler(console_handler)
    
    # Add file handler if configured
    if log_config.log_file:
        file_handler = logging.FileHandler(log_config.log_file)
        file_handler.setLevel(log_config.level)
        file_handler.setFormatter(formatter)
        if log_config.enable_correlation_ids:
            file_handler.addFilter(CorrelationIdFilter())
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> LoggerAdapter:
    """Get a logger with structured logging support.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger adapter with structured logging
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, {})


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """Set correlation ID for the current context.
    
    Args:
        correlation_id: Correlation ID to set (generates new if None)
        
    Returns:
        The correlation ID that was set
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID.
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current context."""
    correlation_id_var.set(None)


class SampledLogger:
    """Logger that samples log messages based on configured rate.
    
    Useful for high-volume operations where logging every request
    would be excessive.
    """
    
    def __init__(self, logger: LoggerAdapter, sample_rate: float = 0.1):
        """Initialize sampled logger.
        
        Args:
            logger: Underlying logger to use
            sample_rate: Fraction of messages to log (0.0 to 1.0)
        """
        self.logger = logger
        self.sample_rate = max(0.0, min(1.0, sample_rate))
    
    def should_sample(self) -> bool:
        """Determine if this log message should be sampled.
        
        Returns:
            True if message should be logged
        """
        return random.random() < self.sample_rate
    
    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message with sampling."""
        if self.should_sample():
            self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message with sampling."""
        if self.should_sample():
            self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message with sampling."""
        if self.should_sample():
            self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs) -> None:
        """Always log error messages (no sampling)."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs) -> None:
        """Always log critical messages (no sampling)."""
        self.logger.critical(msg, *args, **kwargs)


class TimedOperation:
    """Context manager for timing operations and logging duration.
    
    Example:
        with TimedOperation(logger, "load_presentation"):
            presentation = load_pptx(path)
    """
    
    def __init__(
        self,
        logger: LoggerAdapter,
        operation_name: str,
        log_level: int = logging.INFO
    ):
        """Initialize timed operation.
        
        Args:
            logger: Logger to use
            operation_name: Name of the operation
            log_level: Log level to use for duration logging
        """
        self.logger = logger
        self.operation_name = operation_name
        self.log_level = log_level
        self.start_time = 0.0
    
    def __enter__(self) -> "TimedOperation":
        """Start timing the operation."""
        self.start_time = time.time()
        self.logger.log(
            self.log_level,
            f"Starting operation: {self.operation_name}",
            operation=self.operation_name,
            event="operation_start"
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Log operation duration."""
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.logger.log(
                self.log_level,
                f"Operation failed: {self.operation_name} (duration: {duration:.3f}s)",
                operation=self.operation_name,
                duration_seconds=duration,
                event="operation_failed",
                error_type=exc_type.__name__ if exc_type else None
            )
        else:
            self.logger.log(
                self.log_level,
                f"Operation completed: {self.operation_name} (duration: {duration:.3f}s)",
                operation=self.operation_name,
                duration_seconds=duration,
                event="operation_completed"
            )
