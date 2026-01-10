# PowerPoint MCP Server

A Model Context Protocol (MCP) server for PowerPoint (PPTX) file manipulation and automated speaker notes processing. Enables AI agents to interact with PowerPoint presentations through natural language commands.

## Features

- **MCP Server Integration**: Connect AI agents (Cursor, Claude Desktop, VSCode) to PowerPoint files
- **Comprehensive PPTX Operations**: Read, edit, and manage slides, text, images, and speaker notes
- **Automated Notes Processing**: AI-powered translation and summarization of speaker notes
- **Batch Operations**: Process multiple slides efficiently in single atomic transactions
- **Safe Editing**: Zip-based editing preserves animations, transitions, and slide structure
- **Security**: Input validation, workspace boundaries, file size limits
- **Performance**: LRU caching, metrics collection, structured logging

## Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd powerpoint-python-pptx-mcp

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
```

### Running the MCP Server

**Local:**
```bash
python3 -m mcp_server.server
```

**Docker:**
```bash
docker-compose -f docker/docker-compose.yml up -d
```

**Docker Compose (with volume + env):**
```bash
# From repo root
docker compose -f docker/docker-compose.yml up --build

# PPTX files: place them in ./desks on the host; they mount to /workspace/desks in the container.

```

### Connecting AI Agents

#### Containerized (Docker Compose)
- Start the service: `docker compose -f docker/docker-compose.yml up --build`
- Point your MCP client to run the server via `docker exec -i pptx-mcp-container python3 -m mcp_server.server`
- Working directory inside container: `/app`; decks live at `/workspace/desks` (mounted from host `./desks`).

Container MCP config example (Cursor/VS Code):
```json
{
  "mcpServers": {
    "pptx": {
      "command": "docker",
      "args": ["exec", "-i", "pptx-mcp-container", "python3", "-m", "mcp_server.server"],
      "cwd": "/app"
    }
  }
}
```

#### Cursor IDE

Add to Cursor Settings → Features → Model Context Protocol:

```json
{
  "mcpServers": {
    "pptx": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/powerpoint-python-pptx-mcp",
      "env": {
			"PYTHONPATH": "</path/to>/powerpoint-python-pptx-mcp/src"
		}
    }
  }
}
```

#### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows) with the same configuration.

#### GitHub Copilot

The repository includes a GitHub Agent Skill at `.github/skills/pptx-mcp-server/SKILL.md` that provides usage instructions for Copilot agents. The skill will be automatically discovered when working in this repository.

Learn more: [About Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)

## Available Tools

### Read Operations
- `read_presentation_info` - Get presentation metadata (slide count, dimensions, visibility stats)
- `read_slide_content` - Read comprehensive slide content (text, shapes, images)
- `read_slide_text` - Extract all text from a slide
- `read_slide_images` - Get image information
- `read_slides_metadata` - Get metadata for all slides with visibility status

### Notes Operations
- `read_notes` - Read speaker notes from slide(s)
- `read_notes_batch` - Read notes from multiple slides efficiently
- `update_notes` - Update speaker notes (safe zip-based editing)
- `update_notes_batch` - Update multiple slides atomically
- `process_notes_workflow` - Complete workflow with validation and formatting
- `format_notes_structure` - Format notes into short/original structure

### Edit Operations
- `update_slide_text` - Update text in shapes
- `replace_slide_image` - Replace images
- `add_text_box` - Add new text boxes
- `add_image` - Add new images
- `replace_text` - Find and replace text with regex support

### Slide Management
- `add_slide` - Add new slides
- `delete_slide` - Delete slides
- `duplicate_slide` - Duplicate slides
- `change_slide_layout` - Change slide layouts
- `set_slide_visibility` - Hide/show slides

### Health & Monitoring
- `health_check` - Server health and statistics

## Usage Examples

### Through AI Agent (Natural Language)

Once connected to an MCP client, interact using natural language:

- "Read the content from slide 5"
- "Update the notes on slide 3 with this text..."
- "Translate all speaker notes to Vietnamese"
- "Hide slides 10-15"
- "Replace all instances of 'Company A' with 'Company B'"

### Programmatic Usage

```python
from mcp_server.tools.notes_tools import (
    handle_read_notes_batch,
    handle_process_notes_workflow
)

# Read notes from multiple slides
notes = await handle_read_notes_batch({
    "pptx_path": "presentation.pptx",
    "slide_range": "1-10"
})

# Process with AI (translation, summarization)
notes_data = []
for slide in notes["slides"]:
    # Your LLM processing here
    translated = llm.translate(slide["notes"], target="vietnamese")
    short = llm.summarize(translated)
    
    notes_data.append({
        "slide_number": slide["slide_number"],
        "short_text": short,
        "original_text": translated
    })

# Apply all changes atomically
result = await handle_process_notes_workflow({
    "pptx_path": "presentation.pptx",
    "notes_data": notes_data,
    "in_place": True
})
```

## Examples

- `examples/demo_batch_operations.py` - batch notes workflow demo
- `examples/demo_replace_text.py` - text replacement scenarios
- `examples/demo_slide_visibility.py` - slide visibility management

## Operational Scripts

- `scripts/` - operational helpers; see `scripts/README.md` for usage

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     MCP Server                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                    Tools Layer                          │
│  (notes_tools, read_tools, edit_tools, slide_tools)     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│              Service Layer (Dependency Injection)       │
│  PPTXHandler │ NotesEditor │ Validators │ Cache         │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│             Cross-Cutting Concerns                      │
│  Cache │ Logging │ Metrics │ Config │ Rate Limiting     │
└─────────────────────────────────────────────────────────┘
```

### Separation of Concerns

**MCP Server handles:**
- PPTX file operations (read, write, edit)
- File validation and security
- Structure operations (formatting, layout)

**AI Agent handles:**
- Content generation (translation, summarization)
- Language detection
- Natural language understanding
- Orchestrating tool calls

## Configuration

Create a `.env` file or set environment variables:

```bash
# Environment
MCP_ENV=production  # development, staging, or production

# Security
MCP_MAX_FILE_SIZE=1048576000  # 1000MB
MCP_WORKSPACE_DIRS=/path/to/presentations
MCP_ENFORCE_WORKSPACE_BOUNDARY=true

# Performance
MCP_ENABLE_CACHE=true
MCP_CACHE_SIZE=100

# Logging
MCP_LOG_LEVEL=INFO
MCP_LOG_FILE=/var/log/mcp-server.log

```

## Documentation

- **[`.github/skills/pptx-mcp-server/SKILL.md`](.github/skills/pptx-mcp-server/SKILL.md)** - Agent Skill for Copilot and other agents
- **[AGENTS.md](AGENTS.md)** - Quick reference and workflow examples
- **[ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - Technical architecture details
- **[BATCH_OPERATIONS.md](docs/guides/BATCH_OPERATIONS.md)** - Batch processing documentation
- **[SLIDE_VISIBILITY.md](docs/guides/SLIDE_VISIBILITY.md)** - Slide visibility feature guide
- **[Migration Notes](docs/migration-notes.md)** - Repository layout changes

## Testing

```bash
# Quick server test
python3 tests/integration/test_mcp_server.py --quick

# Full test suite
python3 -m pytest tests/ -v

# Specific feature tests
python3 -m pytest tests/integration/test_batch_operations.py
python3 -m pytest tests/integration/test_slide_visibility.py
python3 -m pytest tests/integration/test_replace_text.py
```

## Vietnamese Speaker Notes Guidelines

When generating Vietnamese speaker notes (for AI agents):

- **Address audience as "anh/chị"**
- **Use "chúng ta"** for shared actions/goals
- **Keep sentences short and speakable**
- **Maintain conversational tone**
- **Provide two versions**: Short (30-50% length) + Full/Original

## Troubleshooting

### Server not starting
```bash
# Verify environment
python3 -c "from mcp_server.server import server; print('✓ OK')"

# Run quick test
python3 tests/integration/test_mcp_server.py --quick
```

### Tools not appearing
- Ensure MCP server is properly configured in client settings
- Restart the client application
- Check server logs for errors

### File access issues
- Verify file paths are correct
- Check file permissions
- For Docker: ensure volumes are mounted correctly

### Workspace boundary errors
```bash
# Configure allowed directories
export MCP_WORKSPACE_DIRS="/path/to/presentations"
```

## Security Features

- **Path traversal prevention** with resolution checks
- **File size limits** (default: 1000MB, configurable)
- **Workspace boundaries** restrict file access
- **Input sanitization** with length limits
- **Secure temporary file handling**
- **Structured logging** with sensitive data masking

## Performance

- **LRU caching** for frequently accessed presentations
- **Batch operations** reduce round-trips by 50-100x
- **Parallel processing** for multi-slide operations
- **Lazy loading** of presentation data
- **Metrics collection** for monitoring

## License

**[MIT](LICENSE)**

## Contributing

Contributions welcome! Please:
- Follow existing code style
- Add tests for new features
- Update documentation
- Preserve PPTX structure and formatting

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [GitHub Agent Skills Documentation](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills)
- [python-pptx Documentation](https://python-pptx.readthedocs.io/)
