# AI Agent Guide: Using the PPTX MCP Server

This guide explains how to create and configure an AI agent in VS Code (Agent Custom Mode) to use the PowerPoint MCP Server for automated speaker notes processing and PPTX manipulation.

## Overview

The PPTX MCP Server provides AI agents with tools to:
- Read and update PowerPoint speaker notes
- Translate and summarize notes (especially Vietnamese ↔ English)
- Perform batch operations on multiple slides
- Safely edit PPTX files while preserving animations and transitions

## Setting Up Your AI Agent in VS Code

### Prerequisites

1. VS Code with GitHub Copilot extension
2. PPTX MCP Server running (see main README.md for installation)
3. PowerPoint files accessible to the server

### Configuration

Add to your VS Code MCP settings (Settings → Extensions → Model Context Protocol):

```json
{
  "mcpServers": {
    "pptx": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/powerpoint-python-pptx-mcp",
      "env": {
        "PYTHONPATH": "/path/to/powerpoint-python-pptx-mcp/src",
        "MCP_WORKSPACE_DIRS": "/path/to/your/presentations"
      }
    }
  }
}
```

For Docker:
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

## Available MCP Tools

The server exposes these tools to your AI agent:

### Reading Operations
- `read_presentation_info` - Get metadata (slide count, dimensions)
- `read_slide_content` - Read comprehensive slide content
- `read_notes` - Read speaker notes from a slide
- `read_notes_batch` - Read notes from multiple slides efficiently

### Notes Operations
- `update_notes` - Update speaker notes (safe zip-based editing)
- `update_notes_batch` - Update multiple slides atomically
- `process_notes_workflow` - Complete workflow with validation
- `format_notes_structure` - Format notes into short/original structure

### Other Operations
- `replace_text` - Find and replace text
- `set_slide_visibility` - Hide/show slides
- `health_check` - Check server status

## PPTX Speaker Notes Processing Guidelines

When your AI agent processes speaker notes, follow these guidelines:

### General Principles

- **Only modify speaker notes**, never slide content or layout (unless explicitly requested)
- **Keep empty notes empty** - Don't invent content for slides with empty notes
- **Do NOT add new slides** unless explicitly requested
- Use **MCP server tools** for all operations
- Use **safe zip-based editing** to preserve animations and transitions
- Prefer **batch operations** for multi-slide work (50-100x faster, atomic updates)

### Vietnamese Speaker Notes Style

When generating Vietnamese speaker notes (default language - configurable):

- **Pronouns**: Address audience as **"anh/chị"** (never "bạn" or "quý vị")
- **Collective**: Use **"chúng ta"** for shared actions/goals
- **Tone**: Conversational, casual, suitable for live presentation
- **Sentences**: Keep short and speakable
- **Format**: Simple bullet points; avoid long paragraphs unless requested
- **Facts**: Don't invent product claims or numbers. If citing stats, add "Nguồn:" line
- **Brevity**: Default to comprehensive notes, but reduce length significantly if user requests brevity (e.g., "ngắn gọn thôi")

### Slide Transitions

- **Do NOT** write transition phrases referencing the *next* slide (e.g., "phần tiếp theo...", "sang slide sau...") until user has provided next slide content
- End current slide with neutral wrap-up that stands alone

### Required Notes Structure

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

## Recommended Workflows

### Multi-slide Notes Translation/Summarization

This is the recommended approach for processing multiple slides:

```python
# 1. Read notes in batch
notes = await read_notes_batch(pptx_path="deck.pptx", slide_range="1-20")

# 2. Generate content (AI agent side) - preserve empty notes
notes_data = []
for slide in notes["slides"]:
    if not slide["notes"]:  # Keep empty notes empty
        continue
    
    # Use your LLM to translate and summarize
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

### Single Slide Notes Update

For updating individual slides:

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

## Notes Update Format

When using JSON for batch updates:

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

## Safety Guidelines

- Create backup copy before overwriting PPTX (especially large decks)
- Use `--dry-run` to test processing logic before running with API calls
- Status tracking files allow safe interruption and resume
- Always validate notes structure before applying updates

## Example Agent Instructions

When configuring your AI agent in VS Code, include these instructions:

```markdown
# PPTX Notes Processing Agent

You are an AI agent specialized in processing PowerPoint speaker notes using the PPTX MCP Server.

## Your Capabilities
- Read and analyze PPTX presentations
- Translate speaker notes to Vietnamese with proper tone
- Create short/original note versions
- Process multiple slides efficiently

## Your Guidelines
1. Always read notes in batch for multi-slide operations
2. Keep empty notes empty (don't invent content)
3. Use Vietnamese conversational style: "anh/chị", "chúng ta"
4. Provide both short (30-50%) and original (100%) versions
5. Never modify slide content, only speaker notes
6. Use batch operations for efficiency

## Your Workflow
1. Use read_notes_batch to get all notes
2. Process with your LLM (translation + summarization)
3. Apply all changes atomically with process_notes_workflow
```

## Troubleshooting

### Server Connection Issues
```bash
# Verify server is running
curl http://localhost:8080/health

# Check server logs
docker logs pptx-mcp-container
```

### Tools Not Appearing
- Ensure MCP server is properly configured in VS Code settings
- Restart VS Code after configuration changes
- Check server logs for errors

### File Access Issues
- Verify file paths are correct
- Check file permissions
- For Docker: ensure volumes are mounted correctly
- Verify MCP_WORKSPACE_DIRS includes your presentation directory

## Advanced Features

### Batch Operations Performance

Batch operations are 50-100x faster than individual operations:

```python
# ❌ Slow: 20 individual updates
for i in range(1, 21):
    await update_notes(pptx_path, i, notes[i])

# ✅ Fast: 1 atomic batch update
await update_notes_batch(pptx_path, all_notes_data)
```

### Safe Zip-based Editing

The server uses zip-based editing for notes to preserve animations:

```python
# This preserves all animations and transitions
await update_notes(
    pptx_path="deck.pptx",
    slide_number=5,
    notes_text="...",
    engine="zip"  # Safe editing
)
```

### Status Tracking for Long Operations

For large presentations, use status tracking:

```python
result = await process_notes_workflow(
    pptx_path="large_deck.pptx",
    notes_data=notes_data,
    status_file="progress.json"  # Tracks progress
)
```

## Best Practices

1. **Always use batch operations** for multiple slides
2. **Preserve empty notes** - don't fill them unless requested
3. **Create backups** before overwriting large presentations
4. **Use safe zip-based editing** for notes updates
5. **Test with --dry-run** before running expensive LLM operations
6. **Validate structure** before applying updates
7. **Log operations** for debugging and audit trails

## References

- Main README: [README.md](../README.md)
- Architecture: [docs/architecture/ARCHITECTURE.md](architecture/ARCHITECTURE.md)
- Batch Operations: [docs/guides/BATCH_OPERATIONS.md](guides/BATCH_OPERATIONS.md)
- Agent Quick Reference: [AGENTS.md](../AGENTS.md)
