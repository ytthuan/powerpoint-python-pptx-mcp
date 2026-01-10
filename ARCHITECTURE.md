# MCP Server Architecture

This document describes the architectural improvements made to the PPTX MCP server.

## Overview

The MCP server has been significantly refactored to improve:
- **Maintainability**: Clear separation of concerns with service layer
- **Testability**: Dependency injection with protocol interfaces
- **Performance**: Caching, metrics, and optimizations
- **Security**: Input validation, workspace boundaries, and error handling
- **Observability**: Structured logging, correlation IDs, and metrics

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                          │
│                   (server.py)                           │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Tools Layer                          │
│  (notes_tools, read_tools, edit_tools, slide_tools)    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                  Service Layer                          │
│         (ServiceRegistry, Interfaces)                   │
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │ PPTXHandler  │ NotesEditor  │  Validators  │        │
│  └──────────────┴──────────────┴──────────────┘        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│             Cross-Cutting Concerns                      │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │  Cache   │ Logging  │ Metrics  │  Config  │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
└─────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Configuration (`config.py`)

Centralized configuration management with:
- Environment-based configuration (dev/staging/prod)
- Security settings (file size limits, workspace boundaries)
- Performance settings (caching, rate limiting)
- Logging settings (levels, structured logging, sampling)
- Environment variable support with `.env` file loading

**Usage:**
```python
from mcp_server.config import get_config

config = get_config()
max_size = config.security.max_file_size
enable_cache = config.performance.enable_cache
```

### 2. Exception Hierarchy (`exceptions.py`)

Structured exception hierarchy for better error handling:
- `PPTXError` (base)
- `ValidationError` and subclasses
- `FileOperationError` and subclasses
- `SecurityError` and subclasses
- `ResourceError` and subclasses

**Usage:**
```python
from mcp_server.exceptions import ValidationError, PPTXFileNotFoundError

try:
    result = validate_input(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e.message}", extra=e.details)
    return e.to_dict()  # Structured error response
```

### 3. Structured Logging (`logging_config.py`)

Enhanced logging with:
- Correlation IDs for request tracing
- JSON structured logging
- Sensitive data masking
- Log sampling for high-volume operations
- Timed operations context manager

**Usage:**
```python
from mcp_server.logging_config import get_logger, set_correlation_id, TimedOperation

logger = get_logger(__name__)
correlation_id = set_correlation_id()  # Auto-generated UUID

with TimedOperation(logger, "load_presentation"):
    presentation = load_pptx(path)
```

### 4. Dependency Injection (`services.py`, `interfaces.py`)

Service registry for managing dependencies:
- Protocol-based interfaces for loose coupling
- Singleton and factory registration patterns
- Type-safe service resolution

**Usage:**
```python
from mcp_server.services import get_registry, setup_default_services
from mcp_server.interfaces import ICache, ILogger
from mcp_server.cache import LRUCache

# Setup services
registry = get_registry()
setup_default_services(registry)

# Register custom services
cache = LRUCache(maxsize=100)
registry.register(ICache, cache)

# Resolve services
cache = registry.resolve(ICache)
logger = registry.resolve(ILogger)
```

### 5. Caching (`cache.py`)

LRU cache with TTL support:
- Thread-safe LRU eviction
- Time-to-live (TTL) for entries
- Cache statistics (hits, misses, evictions)
- Specialized PresentationCache for PPTX files

**Usage:**
```python
from mcp_server.cache import LRUCache, PresentationCache

# General purpose cache
cache = LRUCache(maxsize=100, default_ttl=3600)
cache.set("key", value, ttl=1800)
value = cache.get("key")
stats = cache.get_stats()

# Presentation-specific cache
pptx_cache = PresentationCache()
presentation = pptx_cache.get_presentation(path)
if presentation is None:
    presentation = Presentation(path)
    pptx_cache.cache_presentation(path, presentation)
```

### 6. Metrics Collection (`metrics.py`)

Performance monitoring:
- Operation duration tracking
- Success/failure rates
- Counter and gauge metrics
- Percentile calculations (p95, p99)

**Usage:**
```python
from mcp_server.metrics import MetricsCollector

collector = MetricsCollector()

# Record operation
start = time.time()
try:
    perform_operation()
    duration = (time.time() - start) * 1000
    collector.record_operation("operation_name", duration, True)
except Exception:
    duration = (time.time() - start) * 1000
    collector.record_operation("operation_name", duration, False)

# Get metrics
metrics = collector.get_metrics()
print(f"Success rate: {metrics['operations']['operation_name']['success_rate']}")
```

### 7. Enhanced Validators (`utils/validators.py`)

Comprehensive input validation:
- Path traversal prevention
- File size limits
- Workspace boundary enforcement
- Input sanitization and length limits

**Usage:**
```python
from mcp_server.utils.validators import validate_pptx_path, validate_text_input

try:
    path = validate_pptx_path(user_input_path)
    text = validate_text_input(user_text, max_length=1000000)
except ValidationError as e:
    handle_error(e)
```

### 8. Enhanced PPTXHandler (`core/pptx_handler.py`)

Core PPTX operations with caching:
- Optional caching for performance
- Automatic cache invalidation
- Modification tracking
- Lazy loading

**Usage:**
```python
from mcp_server.core.pptx_handler import PPTXHandler
from mcp_server.cache import PresentationCache

cache = PresentationCache()
handler = PPTXHandler(path, cache=cache, enable_cache=True)

# Lazy loads and caches presentation
info = handler.get_presentation_info()

# Modifications tracked and cache invalidated on save
handler.set_slide_hidden(1, True)
handler.save()  # Auto-invalidates cache
```

## Design Patterns Used

### 1. **Dependency Injection**
- ServiceRegistry acts as IoC container
- Protocol-based interfaces for loose coupling
- Testability through mock implementations

### 2. **Strategy Pattern**
- Multiple cache implementations (LRU, NoOp)
- Multiple metrics collectors (MetricsCollector, NoOpMetricsCollector)

### 3. **Factory Pattern**
- Service factory registration in ServiceRegistry
- Lazy initialization of services

### 4. **Singleton Pattern**
- Global config instance
- Global service registry
- Singleton service registration

### 5. **Template Method Pattern**
- PPTXError base class with to_dict() method
- Structured error responses

### 6. **Context Manager Pattern**
- TimedOperation for operation timing
- Resource cleanup on exceptions

## Performance Optimizations

### Caching Strategy
- LRU eviction when cache is full
- TTL-based expiration for freshness
- File modification time tracking for auto-invalidation
- Thread-safe for concurrent access

### Best Practices
1. Always use caching for frequently accessed presentations
2. Set appropriate TTL based on file update frequency
3. Monitor cache statistics for hit rate optimization
4. Use correlation IDs for request tracing
5. Enable metrics collection in production

## Security Features

### Input Validation
- Path traversal prevention using path resolution checks
- File size limits (configurable, default: 100MB)
- Input length limits (default: 1MB for text)
- Workspace boundary enforcement

### Workspace Boundaries
Configure allowed directories:
```bash
export MCP_WORKSPACE_DIRS="/path/to/presentations,/path/to/other"
export MCP_ENFORCE_WORKSPACE_BOUNDARY=true
```

### Sensitive Data Protection
- Automatic masking in logs
- No secrets in exception messages
- Secure temporary file handling

## Configuration

### Environment Variables

```bash
# Environment
MCP_ENV=production  # development, staging, or production

# Security
MCP_MAX_FILE_SIZE=104857600  # 100MB
MCP_WORKSPACE_DIRS=/path/to/workspace
MCP_ENFORCE_WORKSPACE_BOUNDARY=true

# Performance
MCP_ENABLE_CACHE=true
MCP_CACHE_SIZE=100

# Logging
MCP_LOG_LEVEL=INFO
MCP_LOG_FILE=/var/log/mcp-server.log

# Azure (for note processing)
AZURE_AI_PROJECT_ENDPOINT=https://...
MODEL_DEPLOYMENT_NAME=gpt-4
```

### Configuration File (.env)

Create a `.env` file in the project root:
```bash
MCP_ENV=development
MCP_LOG_LEVEL=DEBUG
MCP_ENABLE_CACHE=true
MCP_CACHE_SIZE=50
```

## Testing

### Unit Testing with Dependency Injection

```python
import pytest
from mcp_server.services import ServiceRegistry
from mcp_server.interfaces import ICache, ILogger

class MockCache(ICache):
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def set(self, key, value, ttl=None):
        self.data[key] = value

@pytest.fixture
def registry():
    reg = ServiceRegistry()
    reg.register(ICache, MockCache())
    return reg

def test_with_mock_cache(registry):
    cache = registry.resolve(ICache)
    cache.set("key", "value")
    assert cache.get("key") == "value"
```

## Migration from Old Architecture

See [MIGRATION.md](../MIGRATION.md) for detailed migration guide from scripts to MCP tools.

### Quick Checklist
- [ ] Replace direct script calls with MCP tools
- [ ] Configure environment variables
- [ ] Enable caching for performance
- [ ] Setup structured logging
- [ ] Configure workspace boundaries
- [ ] Enable metrics collection
- [ ] Update error handling to use new exception hierarchy

## Future Improvements

Planned enhancements:
- [x] Tool registry with decorator pattern
- [x] Middleware pipeline for cross-cutting concerns
- [x] Rate limiting middleware
- [x] Health check endpoint
- [ ] Async/await file I/O throughout
- [ ] Distributed caching (Redis)
- [ ] OpenTelemetry integration
- [ ] GraphQL API layer
- [ ] WebSocket support for real-time updates

## Latest Architectural Improvements (2026)

### Tool Registry System (`tools/registry.py`)

Replaces the large if/elif chain in `server.py` with a clean, maintainable decorator-based registry:

**Features:**
- Decorator-based tool registration
- Type-safe handler dispatch
- Easy tool discovery and introspection
- Supports both decorator and direct registration

**Usage:**
```python
from mcp_server.tools.registry import get_tool_registry, register_tool

# Using decorator
@register_tool("my_tool")
async def handle_my_tool(arguments: dict) -> dict:
    return {"result": "success"}

# Direct registration
registry = get_tool_registry()
registry.register_handler("another_tool", handle_another_tool)

# Dispatch
result = await registry.dispatch("my_tool", {"key": "value"})

# Introspection
tools = registry.get_registered_tools()  # ['my_tool', 'another_tool']
is_registered = registry.is_registered("my_tool")  # True
```

### Middleware Pipeline (`middleware.py`)

Provides a composable middleware system for processing tool calls with cross-cutting concerns:

**Built-in Middlewares:**

1. **LoggingMiddleware**: Logs tool calls with correlation IDs
   - Auto-generates correlation IDs for request tracing
   - Logs start, completion, and execution time
   - Error logging with full context

2. **ValidationMiddleware**: Common input validation
   - Validates slide_number (type and range)
   - Validates pptx_path (type and emptiness)
   - Consistent error messages

3. **MetricsMiddleware**: Operation metrics collection
   - Tracks tool call counts
   - Records execution times
   - Success/failure rates

4. **RateLimiterMiddleware**: Rate limiting (see below)

**Usage:**
```python
from mcp_server.middleware import (
    MiddlewarePipeline,
    LoggingMiddleware,
    ValidationMiddleware,
    MetricsMiddleware
)

# Create pipeline
pipeline = MiddlewarePipeline([
    LoggingMiddleware(),
    ValidationMiddleware(),
    MetricsMiddleware()
])

# Execute through pipeline
result = await pipeline.execute("tool_name", args, handler)
```

**Custom Middleware:**
```python
class CustomMiddleware:
    async def __call__(self, name, args, next_handler):
        # Pre-processing
        print(f"Before: {name}")
        
        # Call next middleware/handler
        result = await next_handler(name, args)
        
        # Post-processing
        print(f"After: {name}")
        return result
```

### Rate Limiting (`rate_limiter.py`)

Token bucket rate limiter for preventing abuse:

**Features:**
- Token bucket algorithm implementation
- Configurable rate and burst limits
- Blocking and non-blocking acquire
- Rate limiter middleware for automatic enforcement

**Configuration:**
```python
# In config.py or environment
config.performance.enable_rate_limiting = True
config.performance.max_requests_per_minute = 60
```

**Usage:**
```python
from mcp_server.rate_limiter import TokenBucketRateLimiter

# Create limiter
limiter = TokenBucketRateLimiter(
    rate=60,      # 60 requests
    per=60.0,     # per 60 seconds
    burst=100     # allow bursts up to 100
)

# Blocking acquire (waits for token)
await limiter.acquire()

# Non-blocking try (returns False if no token)
if await limiter.try_acquire():
    process_request()
else:
    return "Rate limit exceeded"

# Check availability
tokens = limiter.get_available_tokens()
wait_time = limiter.get_wait_time(tokens=5)
```

### Lifespan Management (`server.py`)

Added proper startup and shutdown handling:

**Startup:**
- Configuration validation
- Environment logging
- Service initialization logging

**Shutdown:**
- Graceful cleanup
- Cache persistence (if needed)
- Resource release

### Configurable Resource Discovery

Resource search paths can now be configured via environment variable:

```bash
export MCP_RESOURCE_SEARCH_PATHS="/path/to/presentations,/another/path"
```

Or programmatically:
```python
config = get_config()
config.resource_search_paths = [Path("/path/to/presentations")]
```

### Tool Metadata

Tools now include standardized metadata in descriptions:

**Format:**
```
[Category: <category>] [Tags: <tag1>, <tag2>] <description>
```

**Categories:**
- `read`: Read operations
- `edit`: Edit operations
- `notes`: Notes operations
- `slides`: Slide management
- `health`: Health and monitoring

**Example:**
```python
Tool(
    name="read_slide_content",
    description="[Category: read] [Tags: slides, content] Read comprehensive content from a slide"
)
```

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)
- [Structured Logging Best Practices](https://www.loggly.com/ultimate-guide/python-logging-basics/)
- [Python Protocols (PEP 544)](https://peps.python.org/pep-0544/)
