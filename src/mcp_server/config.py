"""Centralized configuration management for MCP server.

This module provides configuration management with environment variable support,
validation, and defaults for different deployment environments.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Set
from urllib.parse import urlparse

from dotenv import load_dotenv


class Environment(Enum):
    """Deployment environment types."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class SecurityConfig:
    """Security-related configuration."""

    # File size limits (in bytes)
    max_file_size: int = 1024 * 1024 * 1024  # 1GB default

    # Allowed file extensions (beyond .pptx)
    allowed_extensions: Set[str] = field(default_factory=lambda: {".pptx", ".pptm"})

    # Workspace boundaries (restrict file access to these directories)
    workspace_dirs: list[Path] = field(default_factory=list)

    # Enable/disable security features
    enforce_workspace_boundary: bool = True
    validate_file_integrity: bool = False  # Checksum validation

    # Input length limits
    max_text_length: int = 1_000_000  # 1MB of text
    max_path_length: int = 4096


@dataclass
class PerformanceConfig:
    """Performance-related configuration."""

    # Caching settings
    enable_cache: bool = True
    cache_size: int = 100  # Max cached presentations
    cache_ttl: int = 3600  # Cache TTL in seconds

    # Async operation settings
    max_concurrent_operations: int = 10
    operation_timeout: int = 300  # 5 minutes default

    # Rate limiting
    enable_rate_limiting: bool = False
    max_requests_per_minute: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration."""

    # Log level
    level: str = "INFO"

    # Structured logging
    enable_structured_logging: bool = True
    enable_correlation_ids: bool = True

    # Log sampling (for high-volume operations)
    enable_sampling: bool = False
    sample_rate: float = 0.1  # Sample 10% of requests

    # Log sensitive data
    log_sensitive_data: bool = False

    # Log file path (optional)
    log_file: Optional[Path] = None


@dataclass
class Config:
    """Main configuration class."""

    # Environment
    environment: Environment = Environment.DEVELOPMENT

    # Feature flags
    enable_dry_run: bool = False
    enable_audit_logging: bool = False
    enable_metrics: bool = False

    # Sub-configurations
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Azure configuration (for note processing)
    azure_endpoint: Optional[str] = None
    azure_deployment_name: Optional[str] = None

    # Azure audio transcription configuration
    audio_endpoint: Optional[str] = None
    audio_deployment: Optional[str] = None
    audio_key: Optional[str] = None
    audio_region: Optional[str] = None
    audio_api_version: str = "2024-10-21"

    # Resource discovery paths
    resource_search_paths: list[Path] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Environment variables:
        - MCP_ENV: Environment (development/staging/production)
        - MCP_MAX_FILE_SIZE: Maximum file size in bytes
        - MCP_WORKSPACE_DIRS: Comma-separated list of workspace directories
        - MCP_LOG_LEVEL: Logging level
        - MCP_ENABLE_CACHE: Enable/disable caching
        - MCP_CACHE_SIZE: Cache size
        - MCP_RESOURCE_SEARCH_PATHS: Comma-separated list of resource search paths
        - AZURE_AI_PROJECT_ENDPOINT: Azure endpoint
        - MODEL_DEPLOYMENT_NAME: Azure model deployment name
        """
        # Load .env file if it exists
        load_dotenv()

        config = cls()

        # Environment
        env_str = os.getenv("MCP_ENV", "development").lower()
        try:
            config.environment = Environment(env_str)
        except ValueError:
            config.environment = Environment.DEVELOPMENT

        # Security settings
        if max_size := os.getenv("MCP_MAX_FILE_SIZE"):
            try:
                config.security.max_file_size = int(max_size)
            except ValueError:
                # Invalid integer format, keep default
                pass

        if workspace_dirs := os.getenv("MCP_WORKSPACE_DIRS"):
            config.security.workspace_dirs = [
                Path(d.strip()) for d in workspace_dirs.split(",") if d.strip()
            ]

        if enforce_boundary := os.getenv("MCP_ENFORCE_WORKSPACE_BOUNDARY"):
            config.security.enforce_workspace_boundary = enforce_boundary.lower() == "true"

        # Performance settings
        if enable_cache := os.getenv("MCP_ENABLE_CACHE"):
            config.performance.enable_cache = enable_cache.lower() == "true"

        if cache_size := os.getenv("MCP_CACHE_SIZE"):
            try:
                config.performance.cache_size = int(cache_size)
            except ValueError:
                # Invalid integer format, keep default
                pass

        # Logging settings
        config.logging.level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()

        if log_file := os.getenv("MCP_LOG_FILE"):
            config.logging.log_file = Path(log_file)

        if enable_structured := os.getenv("MCP_ENABLE_STRUCTURED_LOGGING"):
            config.logging.enable_structured_logging = enable_structured.lower() == "true"

        # Azure settings
        config.azure_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        config.azure_deployment_name = os.getenv("MODEL_DEPLOYMENT_NAME")

        # Azure audio transcription settings
        config.audio_endpoint = os.getenv("AUDIO_ENDPOINT") or os.getenv("SPEECH_ENDPOINT") or os.getenv("ENDPOINT") or None
        config.audio_deployment = os.getenv("AUDIO_DEPLOYMENT") or os.getenv("SPEECH_DEPLOYMENT") or None
        config.audio_key = os.getenv("AUDIO_KEY") or os.getenv("SPEECH_KEY") or None
        config.audio_region = os.getenv("AUDIO_REGION") or os.getenv("SPEECH_REGION") or None
        config.audio_api_version = os.getenv("AUDIO_API_VERSION", config.audio_api_version)

        # Feature flags
        if enable_metrics := os.getenv("MCP_ENABLE_METRICS"):
            config.enable_metrics = enable_metrics.lower() == "true"

        if enable_audit := os.getenv("MCP_ENABLE_AUDIT_LOGGING"):
            config.enable_audit_logging = enable_audit.lower() == "true"

        # Resource search paths
        if search_paths := os.getenv("MCP_RESOURCE_SEARCH_PATHS"):
            config.resource_search_paths = [
                Path(p.strip()) for p in search_paths.split(",") if p.strip()
            ]

        return config

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate security settings
        if self.security.max_file_size <= 0:
            raise ValueError(f"Invalid max_file_size: {self.security.max_file_size}")

        if self.security.max_text_length <= 0:
            raise ValueError(f"Invalid max_text_length: {self.security.max_text_length}")

        # Validate performance settings
        if self.performance.cache_size < 0:
            raise ValueError(f"Invalid cache_size: {self.performance.cache_size}")

        if self.performance.max_concurrent_operations <= 0:
            raise ValueError(
                f"Invalid max_concurrent_operations: {self.performance.max_concurrent_operations}"
            )

        # Validate logging settings
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging.level not in valid_log_levels:
            raise ValueError(
                f"Invalid log level: {self.logging.level}. Must be one of {valid_log_levels}"
            )

        # Validate audio transcription settings when provided
        if self.audio_endpoint or self.audio_deployment or self.audio_key or self.audio_region:
            # We need at least (endpoint OR region) AND key
            if not (self.audio_endpoint or self.audio_region) or not self.audio_key:
                raise ValueError("Audio transcription configuration is incomplete. Need (SPEECH_ENDPOINT or SPEECH_REGION) and SPEECH_KEY.")

            if self.audio_endpoint:
                parsed_endpoint = urlparse(self.audio_endpoint)
                if parsed_endpoint.scheme != "https":
                    raise ValueError(
                        "Invalid audio_endpoint. Expected a secure HTTPS URL (e.g., https://<resource>.openai.azure.com)"
                    )

            if not self.audio_api_version:
                raise ValueError("audio_api_version must be provided when audio transcription is set.")

        # Validate workspace directories exist (if enforcement is enabled)
        if self.security.enforce_workspace_boundary and self.security.workspace_dirs:
            for workspace_dir in self.security.workspace_dirs:
                if not workspace_dir.exists():
                    raise ValueError(f"Workspace directory does not exist: {workspace_dir}")


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        Config: The global configuration instance
    """
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.validate()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance.

    Args:
        config: The configuration to set
    """
    global _config
    config.validate()
    _config = config


def reset_config() -> None:
    """Reset the global configuration to None (useful for testing)."""
    global _config
    _config = None
