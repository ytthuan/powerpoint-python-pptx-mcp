---
applyTo: "tests/**/*.py"
---

# Testing Guidelines

These instructions apply to all test files in the `tests/` directory.

## Testing principles

- **Test behavior, not implementation** - Focus on what code does, not how
- **Test both success and error cases** - Happy path AND edge cases
- **Keep tests independent** - No test should depend on another
- **Clean up resources** - Use fixtures and teardown to clean up
- **Make tests deterministic** - No flaky tests allowed

## Test structure pattern

```python
import pytest
from mcp_server.tools.example import handle_example

@pytest.mark.unit  # or @pytest.mark.integration
@pytest.mark.asyncio
async def test_example_success(sample_pptx_path):
    """Test successful example operation.
    
    Given: Valid inputs
    When: Tool is invoked
    Then: Operation succeeds with expected result
    """
    # Arrange
    arguments = {
        "pptx_path": sample_pptx_path,
        "param": "value"
    }
    
    # Act
    result = await handle_example(arguments)
    
    # Assert
    assert result["success"] is True
    assert "data" in result
    assert result["data"]["field"] == "expected_value"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_example_validation_error(sample_pptx_path):
    """Test error handling for invalid input.
    
    Given: Invalid parameter
    When: Tool is invoked
    Then: ValidationError is raised or error response returned
    """
    # Arrange
    arguments = {
        "pptx_path": sample_pptx_path,
        "param": None  # Invalid
    }
    
    # Act
    result = await handle_example(arguments)
    
    # Assert
    assert result["success"] is False
    assert result["error_type"] == "validation_error"
```

## Pytest markers

Always use appropriate markers:
- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests with file I/O or multiple components
- `@pytest.mark.slow` - Tests that take >1 second
- `@pytest.mark.benchmark` - Performance benchmarks
- `@pytest.mark.security` - Security-focused tests

## Fixtures

Use fixtures for common setup:

```python
@pytest.fixture
def sample_pptx_path(tmp_path):
    """Create a sample PPTX file for testing."""
    pptx_path = tmp_path / "sample.pptx"
    # Create presentation...
    return str(pptx_path)

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test."""
    yield
    # Cleanup code here
```

## Test coverage requirements

- **Minimum 85% code coverage** for all new code
- **100% coverage** for validation and security code
- Use `pytest --cov=src/mcp_server --cov-report=html` to check

## What to test

### Unit tests
- Input validation logic
- Business logic functions
- Error handling paths
- Edge cases and boundary conditions
- Data transformations

### Integration tests
- End-to-end tool workflows
- File I/O operations
- Multiple components working together
- Error propagation across layers

## Test naming conventions

```python
# Pattern: test_<what>_<condition>_<expected_result>
def test_read_notes_valid_slide_returns_notes()
def test_read_notes_invalid_slide_raises_error()
def test_update_notes_empty_input_returns_error()
```

## Async testing

Always use `async def` for tests that call async code:

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await some_async_function()
    assert result is not None
```

## Mocking external dependencies

```python
from unittest.mock import Mock, patch, AsyncMock

@pytest.mark.unit
async def test_with_mock(mocker):
    """Test with mocked service."""
    # Mock the service
    mock_service = AsyncMock()
    mock_service.operation.return_value = "mocked_result"
    
    # Use mocker.patch to replace real service
    mocker.patch("module.get_service", return_value=mock_service)
    
    # Test code...
    result = await handle_operation()
    
    # Verify mock was called
    mock_service.operation.assert_called_once()
```

## Parametrized tests

Use parametrize for testing multiple inputs:

```python
@pytest.mark.parametrize("slide_number,expected", [
    (1, True),
    (5, True),
    (0, False),    # Invalid
    (-1, False),   # Invalid
    (999, False),  # Out of range
])
@pytest.mark.asyncio
async def test_slide_validation(slide_number, expected):
    """Test slide number validation."""
    result = validate_slide_number(slide_number, max_slides=10)
    assert result == expected
```

## Test data management

- Use `tmp_path` fixture for temporary files
- Create minimal test data (don't use production files)
- Store test fixtures in `tests/fixtures/`
- Clean up all test data in teardown

## Performance testing

```python
@pytest.mark.benchmark
def test_batch_operation_performance(benchmark):
    """Benchmark batch operation performance."""
    result = benchmark(batch_operation, data=large_dataset)
    assert result is not None
```

## Debugging tests

```python
# Run single test with verbose output
pytest tests/unit/test_example.py::test_function -v

# Run with print statements visible
pytest -s tests/unit/test_example.py

# Run with debugger on failure
pytest --pdb tests/unit/test_example.py
```

## Common anti-patterns to avoid

- ❌ Testing private methods directly (test through public API)
- ❌ Tests that depend on execution order
- ❌ Tests with sleep() calls (use proper async/await)
- ❌ Tests that modify global state
- ❌ Tests without assertions
- ❌ Tests that test multiple unrelated things

## Before committing changes

**ALWAYS** run linting and formatting checks before committing:

```bash
# Format code
black tests/ --line-length=100

# Check linting
flake8 tests/ --max-line-length=100 --extend-ignore=E203,W503

# Verify formatting
black --check --line-length 100 tests/
```

Ensure all checks pass before committing to avoid CI/CD pipeline failures.
