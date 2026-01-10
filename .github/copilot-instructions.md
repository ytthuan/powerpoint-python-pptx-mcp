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
- Document the fix in commit message

### When refactoring
- Ensure all tests pass before and after
- Keep changes incremental and focused
- Update related documentation
- Do not change public API without discussion

## PPTX Speaker Notes Processing

This is a **core feature** of the project. Follow these guidelines carefully when working with speaker notes.

### General principles
- **Only modify speaker notes**, never slide content or layout (unless explicitly requested)
- **Keep empty notes empty** (do not invent content for empty notes)
- **Do NOT add new slides** unless user explicitly requests it
- Use **MCP server tools** for all operations (e.g., `read_notes_batch`, `update_notes_batch`, `process_notes_workflow`)
- Use **safe zip-based editing** (`--engine zip`) to preserve animations and transitions
- Avoid `python-pptx` write path unless explicitly requested (rewrites entire PPTX)
- Prefer **batch operations** for multi-slide work (atomic updates, 50-100x faster)

### Vietnamese speaker notes style

When generating Vietnamese speaker notes (default language - configurable):

- **Pronouns**: Address audience as **"anh/chị"** (never "bạn" or "quý vị")
- **Collective**: Use **"chúng ta"** for shared actions/goals
- **Tone**: Conversational, casual, suitable for live presentation
- **Sentences**: Keep short and speakable
- **Format**: Simple bullet points; avoid long paragraphs unless requested
- **Facts**: Don't invent product claims or numbers. If citing stats, add "Nguồn:" line
- **Brevity**: Default to comprehensive notes, but when user explicitly requests brevity (e.g., "ngắn gọn thôi"), reduce length significantly while preserving key points

### Slide transitions
- **Do NOT** write transition phrases referencing the *next* slide (e.g., "phần tiếp theo...", "sang slide sau...") until user has provided next slide content
- End current slide with neutral wrap-up that stands alone

### Required notes structure

**Always provide TWO versions** of each note:

```
- Short version:
[Brief summary - 30-50% of original length, key points only]

- Original:
[Full translation/explanation with all details, examples, and explanations]
```

**Both versions must:**
- Use "anh/chị" and "chúng ta" pronouns (for Vietnamese)
- Be in conversational, speakable language
- Follow the exact format above

### Recommended workflows

#### Multi-slide notes (translation/summarization)
```python
# 1. Read notes in batch
notes = await read_notes_batch(pptx_path="deck.pptx", slide_range="1-20")

# 2. Generate content (LLM side) - preserve empty notes
notes_data = []
for slide in notes["slides"]:
    if not slide["notes"]:  # Keep empty notes empty
        continue
    translated = llm.translate(slide["notes"], target="vietnamese")
    short = llm.summarize(translated, length_percent=40)
    notes_data.append({
        "slide_number": slide["slide_number"],
        "short_text": short,
        "original_text": translated,
    })

# 3. Apply atomically (server side)
result = await process_notes_workflow(
    pptx_path="deck.pptx",
    notes_data=notes_data,
    in_place=True  # Create backup before overwriting
)
```

#### Single slide notes update
```python
# Read single slide note
note = await read_notes(pptx_path="deck.pptx", slide_number=5)

# Update with formatted structure
await update_notes(
    pptx_path="deck.pptx",
    slide_number=5,
    notes_text="- Short version:\n...\n\n- Original:\n...",
    engine="zip"  # Safe editing
)
```

### Notes update format

When using JSON for updates:
```json
{
  "slides": [
    {
      "slide": 63,
      "notes": "- Short version:\n[brief content]\n\n- Original:\n[full content]"
    }
  ]
}
```

### Safety guidelines
- Create backup copy before overwriting PPTX (especially large decks)
- Use `--dry-run` to test processing logic before running with API calls
- Status tracking files allow safe interruption and resume
- Always validate notes structure before applying updates

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
- **[ARCHITECTURE.md](../docs/architecture/ARCHITECTURE.md)** - Technical architecture details
- **[BATCH_OPERATIONS.md](../docs/guides/BATCH_OPERATIONS.md)** - Batch processing documentation
- **[SLIDE_VISIBILITY.md](../docs/guides/SLIDE_VISIBILITY.md)** - Slide visibility feature guide
