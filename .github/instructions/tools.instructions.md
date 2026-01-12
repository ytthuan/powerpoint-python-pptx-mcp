---
applyTo: "src/mcp_server/tools/**/*.py"
---

# MCP Tools Development

These instructions apply to all MCP tool implementations in `src/mcp_server/tools/`.

## Critical requirements

- **All tools must validate inputs** using `mcp_server.utils.validators`
- **All tools must use async/await** (never block the event loop)
- **All tools must return structured dictionaries** with `success` key
- **All file paths must be validated** (no path traversal)
- **All tools must handle errors gracefully** with custom exceptions

## Tool structure pattern

```python
from typing import Dict, Any
from mcp_server.utils.validators import validate_file_path, validate_slide_number
from mcp_server.exceptions import ValidationError, FileOperationError

async def handle_tool_name(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Handle MCP tool request for [specific operation].
    
    Args:
        arguments: Tool arguments from MCP client containing:
            - required_param: Description
            - optional_param: Description (optional)
        
    Returns:
        Dictionary with:
            - success (bool): Operation success status
            - data (Any): Tool result data
            - message (str): Optional status message
        
    Raises:
        ValidationError: If arguments are invalid
        FileOperationError: If file operation fails
    """
    try:
        # 1. Validate inputs
        pptx_path = arguments.get("pptx_path")
        validate_file_path(pptx_path)
        
        # 2. Get service from container
        service = get_service_from_container()
        
        # 3. Perform operation
        result = await service.operation(pptx_path)
        
        # 4. Return structured result
        return {
            "success": True,
            "data": result,
            "message": "Operation completed successfully"
        }
        
    except ValidationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "validation_error"
        }
    except Exception as e:
        # Log full exception details server-side for debugging
        logger.error(f"Unexpected error in tool", exc_info=True)
        return {
            "success": False,
            "error": "An unexpected internal error occurred. Please try again later.",
            "error_type": "internal_error"
        }
```

## Input validation checklist

- [ ] All required arguments extracted and validated
- [ ] File paths validated with `validate_file_path`
- [ ] Slide numbers validated with `validate_slide_number`
- [ ] String lengths checked for reasonable limits
- [ ] Workspace boundaries enforced
- [ ] File size limits respected

## Error handling

- Use custom exceptions from `mcp_server.exceptions`
- Never expose internal errors to clients
- Log errors with structured context
- Return user-friendly error messages
- Include error_type in error responses

## Logging

```python
import logging
logger = logging.getLogger(__name__)

# Log tool invocation
logger.info("Tool invoked", extra={
    "tool": "tool_name",
    "pptx_path": pptx_path,
    "user_id": "masked"
})

# Log errors
logger.error("Tool failed", extra={
    "tool": "tool_name",
    "error": str(e),
    "error_type": type(e).__name__
}, exc_info=True)
```

## Performance considerations

- Use LRU cache for frequently accessed data
- Prefer batch operations over individual calls
- Lazy load data when possible
- Monitor memory usage for large files
- Use async operations for I/O

## Testing requirements

- Write unit tests for validation logic
- Write integration tests for tool handlers
- Test both success and error cases
- Mock external dependencies
- Use fixtures for common setup

## Before committing changes

**ALWAYS** run linting and formatting checks before committing:

```bash
# Format code
black src/mcp_server/tools/ --line-length=100

# Check linting
flake8 src/mcp_server/tools/ --max-line-length=100 --extend-ignore=E203,W503

# Verify formatting
black --check --line-length 100 src/mcp_server/tools/
```

Ensure all checks pass before committing to avoid CI/CD pipeline failures.
