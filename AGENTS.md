# Agent Quick Reference - Development

> 📖 **For using this MCP server in your AI agent**, see [docs/guides/AI_AGENT_GUIDE.md](docs/guides/AI_AGENT_GUIDE.md)
> 
> 📖 **For GitHub Copilot Skills**, see [.github/skills/pptx-mcp-server/SKILL.md](.github/skills/pptx-mcp-server/SKILL.md)

## What this repo is for

A **PowerPoint MCP Server** for automated PPTX processing, with a primary focus on **speaker notes** workflows (read/translate/summarize/update).

This file provides quick reference for **developing** the server.

## Development Focus

When developing speaker notes features:

- **Server-side processing**: Implement tools for reading, validating, and updating notes
- **Safe editing**: Use zip-based editing to preserve animations and transitions
- **Batch operations**: Design for efficient multi-slide processing (50-100x faster)
- **Validation**: Ensure all inputs are validated and sanitized
- **Error handling**: Provide clear error messages and handle edge cases

## Implementation Guidelines

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

### Zip-based Editing Pattern

For notes updates, prefer zip-based editing over python-pptx write path:

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

- Accept lists/ranges of slides in single request
- Process all operations before writing
- Make updates atomic (all or nothing)
- Provide progress tracking for large operations

### Vietnamese Text Support

When implementing features with Vietnamese text:

- **Text encoding**: Ensure proper Unicode/UTF-8 support
- **Validation**: Don't validate content based on English-only assumptions
- **Testing**: Include Vietnamese text in test cases

## Setup (local dev)

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip3 install -r requirements.txt
pip3 install -e .

# Set workspace directory
export MCP_WORKSPACE_DIRS=/path/to/presentations
```

## Key Development Commands

```bash
# Run server
python3 -m mcp_server.server

# Run tests
python3 -m pytest tests/ -v

# Test specific features
python3 -m pytest tests/integration/test_notes_tools.py -v
python3 -m pytest tests/integration/test_batch_operations.py -v

# Lint and format
black src/ tests/ --line-length=100
mypy src/ --strict --ignore-missing-imports
```

## Documentation

- **[Copilot Instructions](.github/copilot-instructions.md)** - Complete development guidelines
- **[Agent Personas](.github/agents/AGENTS.md)** - Specialized development agents
- **[Path-specific Instructions](.github/instructions/)** - Code-level patterns
- **[AI Agent Guide](docs/guides/AI_AGENT_GUIDE.md)** - How to **use** this server in your AI agent
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - Technical architecture
- **[Batch Operations](docs/guides/BATCH_OPERATIONS.md)** - Batch processing guide
