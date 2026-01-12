# GitHub Copilot Instructions

## Project context

This repository is a **Model Context Protocol (MCP) server for PowerPoint (PPTX) file manipulation**. It enables AI agents to interact with PowerPoint presentations through natural language commands, with a primary focus on automated speaker notes processing.

The project includes:
- MCP server implementation for PPTX operations (read, edit, slide management)
- Automated speaker notes processing (translation, summarization, batch updates)
- Safe zip-based editing that preserves animations and transitions
- Comprehensive validation, caching, and security features
- Support for multi-language note processing (Vietnamese/English - configurable)

Primary audience: Developers building AI-powered presentation tools and content creators working with PowerPoint presentations.

## Tech stack

- **Language**: Python 3.11+ (strictly typed with mypy)
- **Core libraries**: 
  - `python-pptx` for PPTX manipulation
  - `lxml` for XML processing
  - `mcp` for Model Context Protocol server
  - `Pillow` for image handling
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Code quality**: black, isort, flake8, mypy, bandit, interrogate
- **Dependency management**: pip, requirements.txt
- **Pre-commit hooks**: Configured for automatic code quality checks

## Build, test, and lint commands

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip3 install -r requirements.txt
pip3 install -e .
```

### Running the server
```bash
python3 -m mcp_server.server
```

### Testing
```bash
# Full test suite
python3 -m pytest tests/ -v

# Quick server test
python3 tests/integration/test_mcp_server.py --quick

# Specific feature tests
python3 -m pytest tests/integration/test_batch_operations.py
python3 -m pytest tests/integration/test_slide_visibility.py

# With coverage report
python3 -m pytest --cov=src/mcp_server --cov-report=html
```

### Linting and formatting
```bash
# Format code
black src/ tests/ --line-length=100
isort src/ tests/ --profile black --line-length 100

# Lint
flake8 src/ tests/ --max-line-length=100 --extend-ignore=E203,W503

# Type checking
mypy src/ --strict --ignore-missing-imports

# Security checks
bandit -r src/ -c pyproject.toml

# Docstring coverage
interrogate src/ --config=pyproject.toml

# Run all pre-commit hooks
pre-commit run --all-files
```

## Coding conventions

### Python style
- **Line length**: 100 characters (enforced by black)
- **Type hints**: Required for all functions (enforced by mypy strict mode)
- **Imports**: Sorted with isort using black profile
- **Docstrings**: Google-style docstrings required (minimum 80% coverage)
- **Naming**: 
  - `snake_case` for functions, variables, and methods
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - Private methods/attributes prefixed with `_`

### Architecture patterns
- **Dependency injection**: Use `ServiceContainer` for dependency management
- **Separation of concerns**: Tools layer → Service layer → Core components
- **Error handling**: Use custom exceptions from `mcp_server.exceptions`
- **Async/await**: Use async functions for I/O operations
- **Validation**: Always validate inputs with `mcp_server.utils.validators`

### File organization
- MCP tools: `src/mcp_server/tools/`
- Core services: `src/mcp_server/services.py`
- PPTX handler: `src/mcp_server/core/pptx_handler.py`
- Tests: `tests/` (mirror src structure)

### Testing conventions
- Test files must match `test_*.py` pattern
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Aim for 85%+ code coverage
- Test both success and error cases
- Use fixtures for common setup

## Boundaries and constraints

### What NOT to do
- **Never** commit secrets, API keys, or credentials to version control
- **Never** modify working code without tests to verify behavior
- **Never** use `any` type in Python (use proper type hints)
- **Never** disable type checking or linting without documented reason
- **Never** remove existing tests unless replacing with better ones
- **Never** add dependencies without checking for security vulnerabilities
- **Do not** change `.github/copilot-instructions.md` without user approval
- **Do not** modify `.github/workflows/` without explicit permission

### Security requirements
- All file paths must be validated (no path traversal)
- Enforce workspace boundaries (MCP_WORKSPACE_DIRS)
- File size limits enforced (default 1000MB)
- Input sanitization required for all user inputs
- Sensitive data must be masked in logs

### Performance requirements
- Use LRU caching for frequently accessed presentations
- Prefer batch operations for multi-slide updates (50-100x faster)
- Lazy load presentation data when possible
- Monitor memory usage for large PPTX files

## Development guidelines

### Before committing code changes

**ALWAYS** run the following checks before committing any code changes:

```bash
# 1. Format code with Black
black src/ tests/ examples/ scripts/ --line-length=100

# 2. Check imports with isort
isort src/ tests/ examples/ scripts/ --profile black --line-length 100

# 3. Run flake8 linting
flake8 src tests examples scripts --max-line-length=100 --extend-ignore=E203,W503

# 4. Verify Black formatting (should show no changes needed)
black --check --line-length 100 src tests examples scripts
```

These checks ensure:
- Code formatting is consistent with project standards
- No linting errors are introduced
- CI/CD pipeline will pass the lint and format checks

**If any of these checks fail, fix the issues before committing.**

### When adding new features
- Add comprehensive tests (unit + integration) before implementation
- Update documentation in README.md and relevant docs/
- Follow existing patterns in the codebase
- Use dependency injection via ServiceContainer
- Add appropriate logging with structured context
- Consider security implications (validation, boundaries)
- Measure performance impact for operations on large files

### When fixing bugs
- Add a regression test that reproduces the bug
- Fix the minimal code required
- Verify existing tests still pass
- **Run all linting and formatting checks** (see "Before committing code changes" section)
- Document the fix in commit message

### When refactoring
- Ensure all tests pass before and after
- **Run all linting and formatting checks** (see "Before committing code changes" section)
- Keep changes incremental and focused
- Update related documentation
- Do not change public API without discussion

## PPTX Speaker Notes Processing

This is a **core feature** of the project that you will be developing and maintaining.

### Development Focus

When working on speaker notes functionality:

- **Server-side processing**: Implement tools for reading, validating, and updating notes
- **Safe editing**: Use zip-based editing to preserve animations and transitions
- **Batch operations**: Design for efficient multi-slide processing (50-100x faster than individual ops)
- **Validation**: Ensure all inputs are validated and sanitized
- **Error handling**: Provide clear error messages and handle edge cases

### Vietnamese Language Support

The server supports Vietnamese speaker notes formatting. When implementing features:

- **Text encoding**: Ensure proper Unicode/UTF-8 support for Vietnamese characters
- **Validation**: Don't validate content based on English-only assumptions
- **Testing**: Include Vietnamese text in test cases
- **Documentation**: Document language-specific requirements

### Notes Format Structure

The server supports a two-version notes format:

```
- Short version:
[Brief summary - 30-50% of original length]

- Original:
[Full translation/explanation with all details]
```

When implementing validation or formatting features:
- Validate this structure exists when required
- Don't modify the format structure itself
- Support both structured and unstructured notes

### Zip-based Editing Implementation

For notes updates, prefer zip-based editing over python-pptx write path:

**Why zip-based editing:**
- Preserves animations and transitions
- Faster for notes-only updates
- Reduces risk of PPTX corruption
- Only modifies necessary XML files

**Implementation pattern:**
```python
import zipfile
from lxml import etree

def update_notes_zip(pptx_path: str, slide_number: int, notes_text: str):
    """Update notes using zip-based editing."""
    with zipfile.ZipFile(pptx_path, 'r') as zip_in:
        notes_path = f'ppt/notesSlides/notesSlide{slide_number}.xml'
        # Read, modify XML, write back
        # Only touch notesSlide*.xml files
```

### Batch Operations Design

Design tools to support batch operations:

**Key principles:**
- Accept lists/ranges of slides in single request
- Process all operations before writing
- Make updates atomic (all or nothing)
- Provide progress tracking for large operations
- Use efficient data structures (avoid O(n²) operations)

**Example API:**
```python
async def handle_update_notes_batch(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Update multiple slides in single atomic operation."""
    # 1. Validate all inputs first
    # 2. Process all slides
    # 3. Apply all changes atomically
    # 4. Return success/failure for entire batch
```

### Safety and Validation

When implementing notes features:

- **Always validate slide numbers** against presentation bounds
- **Check file exists** before operations
- **Validate notes text length** to prevent memory issues
- **Create backups** before in-place modifications
- **Verify PPTX integrity** after modifications
- **Handle encoding issues** gracefully

### Performance Considerations

- Use **LRU caching** for frequently accessed presentations
- Implement **lazy loading** for presentation data
- Monitor **memory usage** for large PPTX files
- Profile **batch operations** vs individual operations
- Optimize **XML parsing** for notes slides

## Common commands

### Python environment
```bash
# Always use python3 and pip3
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```

### Docker
```bash
# Build and run with Docker Compose
docker compose -f docker/docker-compose.yml up --build

# PPTX files: place in ./desks on host; mount to /workspace/desks in container
```

## Documentation references

- **[README.md](../README.md)** - Project overview and quick start
- **[AGENTS.md](../AGENTS.md)** - Quick reference for AI agents
- **[.github/skills/pptx-mcp-server/SKILL.md](.github/skills/pptx-mcp-server/SKILL.md)** - Agent Skill for Copilot
- **[docs/guides/AI_AGENT_GUIDE.md](../docs/guides/AI_AGENT_GUIDE.md)** - Complete guide for creating AI agents that use this MCP server
- **[ARCHITECTURE.md](../docs/architecture/ARCHITECTURE.md)** - Technical architecture details
- **[BATCH_OPERATIONS.md](../docs/guides/BATCH_OPERATIONS.md)** - Batch processing documentation
- **[SLIDE_VISIBILITY.md](../docs/guides/SLIDE_VISIBILITY.md)** - Slide visibility feature guide

## For AI Agent Developers

If you're looking for instructions on **how to use this MCP server** in your AI agent (VS Code Agent Custom Mode, Cursor, Claude Desktop, etc.), see:
- **[docs/guides/AI_AGENT_GUIDE.md](../docs/guides/AI_AGENT_GUIDE.md)** - Complete guide with setup, configuration, and usage examples

This file (copilot-instructions.md) is for **developing the MCP server itself**, not for using it.
