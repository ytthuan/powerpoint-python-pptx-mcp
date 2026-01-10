"""Unit tests for configuration management module."""

import os
import pytest
from pathlib import Path

from mcp_server.config import (
    Config,
    Environment,
    SecurityConfig,
    PerformanceConfig,
    LoggingConfig,
    get_config,
    set_config,
    reset_config,
)


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment before each test."""
    # Remove all MCP_* environment variables
    for key in list(os.environ.keys()):
        if key.startswith("MCP_"):
            monkeypatch.delenv(key, raising=False)
    reset_config()
    yield
    reset_config()


class TestSecurityConfig:
    """Tests for SecurityConfig dataclass."""

    def test_default_values(self):
        """Test default security configuration values."""
        config = SecurityConfig()
        assert config.max_file_size == 1024 * 1024 * 1024  # 1GB
        assert ".pptx" in config.allowed_extensions
        assert ".pptm" in config.allowed_extensions
        assert config.enforce_workspace_boundary is True
        assert config.max_text_length == 1_000_000
        assert config.max_path_length == 4096


class TestPerformanceConfig:
    """Tests for PerformanceConfig dataclass."""

    def test_default_values(self):
        """Test default performance configuration values."""
        config = PerformanceConfig()
        assert config.enable_cache is True
        assert config.cache_size == 100
        assert config.cache_ttl == 3600
        assert config.max_concurrent_operations == 10


class TestLoggingConfig:
    """Tests for LoggingConfig dataclass."""

    def test_default_values(self):
        """Test default logging configuration values."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.enable_structured_logging is True
        assert config.enable_correlation_ids is True


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self, clean_env):
        """Test default configuration."""
        config = Config()
        assert config.environment == Environment.DEVELOPMENT
        assert isinstance(config.security, SecurityConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.logging, LoggingConfig)

    def test_from_env_development(self, clean_env, monkeypatch):
        """Test loading development environment from env."""
        monkeypatch.setenv("MCP_ENV", "development")
        config = Config.from_env()
        assert config.environment == Environment.DEVELOPMENT

    def test_from_env_production(self, clean_env, monkeypatch):
        """Test loading production environment from env."""
        monkeypatch.setenv("MCP_ENV", "production")
        config = Config.from_env()
        assert config.environment == Environment.PRODUCTION

    def test_from_env_max_file_size(self, clean_env, monkeypatch):
        """Test loading max file size from env."""
        monkeypatch.setenv("MCP_MAX_FILE_SIZE", "209715200")  # 200MB
        config = Config.from_env()
        assert config.security.max_file_size == 209715200

    def test_from_env_invalid_max_file_size(self, clean_env, monkeypatch):
        """Test invalid max file size falls back to default."""
        monkeypatch.setenv("MCP_MAX_FILE_SIZE", "invalid")
        config = Config.from_env()
        assert config.security.max_file_size == 1024 * 1024 * 1024  # Default

    def test_from_env_workspace_dirs(self, clean_env, monkeypatch):
        """Test loading workspace directories from env."""
        monkeypatch.setenv("MCP_WORKSPACE_DIRS", "/path/one,/path/two")
        config = Config.from_env()
        assert len(config.security.workspace_dirs) == 2
        assert Path("/path/one") in config.security.workspace_dirs
        assert Path("/path/two") in config.security.workspace_dirs

    def test_from_env_cache_settings(self, clean_env, monkeypatch):
        """Test loading cache settings from env."""
        monkeypatch.setenv("MCP_ENABLE_CACHE", "false")
        monkeypatch.setenv("MCP_CACHE_SIZE", "50")
        config = Config.from_env()
        assert config.performance.enable_cache is False
        assert config.performance.cache_size == 50

    def test_from_env_log_level(self, clean_env, monkeypatch):
        """Test loading log level from env."""
        monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
        config = Config.from_env()
        assert config.logging.level == "DEBUG"

    def test_validate_success(self):
        """Test successful validation."""
        config = Config()
        config.validate()  # Should not raise

    def test_validate_invalid_max_file_size(self):
        """Test validation fails for invalid max file size."""
        config = Config()
        config.security.max_file_size = -1
        with pytest.raises(ValueError, match="Invalid max_file_size"):
            config.validate()

    def test_validate_invalid_cache_size(self):
        """Test validation fails for invalid cache size."""
        config = Config()
        config.performance.cache_size = -1
        with pytest.raises(ValueError, match="Invalid cache_size"):
            config.validate()

    def test_validate_invalid_log_level(self):
        """Test validation fails for invalid log level."""
        config = Config()
        config.logging.level = "INVALID"
        with pytest.raises(ValueError, match="Invalid log level"):
            config.validate()


class TestGlobalConfig:
    """Tests for global configuration management."""

    def test_get_config_singleton(self, clean_env):
        """Test get_config returns singleton."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config(self, clean_env):
        """Test setting global configuration."""
        custom_config = Config()
        custom_config.environment = Environment.PRODUCTION
        set_config(custom_config)

        retrieved_config = get_config()
        assert retrieved_config is custom_config
        assert retrieved_config.environment == Environment.PRODUCTION

    def test_reset_config(self, clean_env):
        """Test resetting global configuration."""
        config1 = get_config()
        reset_config()
        config2 = get_config()
        assert config1 is not config2

    def test_set_config_validates(self, clean_env):
        """Test set_config validates configuration."""
        invalid_config = Config()
        invalid_config.security.max_file_size = -1

        with pytest.raises(ValueError):
            set_config(invalid_config)
