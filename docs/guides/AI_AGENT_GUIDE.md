# AI Agent Guide: Using the PPTX MCP Server

This guide explains how to create and configure an AI agent in VS Code (Agent Custom Mode) to use the PowerPoint MCP Server for automated speaker notes processing and PPTX manipulation.

## Overview

The PPTX MCP Server provides AI agents with tools to:
- Read and update PowerPoint speaker notes
- Manipulate slides (add, delete, duplicate, hide/show)
- Update slide content (text, images, shapes)
- Translate and summarize notes (especially Vietnamese ↔ English)
- **Transcribe audio from embedded videos** (using Azure OpenAI / Whisper)
- Perform batch operations on multiple slides
- Safely edit PPTX files while preserving animations and transitions

## Setting Up Your AI Agent in VS Code

### Prerequisites

1. VS Code with GitHub Copilot extension, Cursor
2. PPTX MCP Server running (see main README.md for installation)
3. PowerPoint files accessible to the server
4. **(LLM & Transcription tools)**:
   - For Note LLM: Export `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME`.
   - For Transcription: Export `SPEECH_ENDPOINT` (or `SPEECH_REGION`), `SPEECH_KEY`, and `SPEECH_DEPLOYMENT`.
   - Authentication uses `DefaultAzureCredential` for Foundry or API keys for Speech. Tools are skipped if configuration is missing.

### Configuring the Agent
## Available MCP Tools

The server exposes these tools to your AI agent:

### Presentation & Metadata
- `read_presentation_info` - Get metadata (slide count, dimensions, visibility stats)
- `read_slides_metadata` - Get metadata for all slides including visibility status
- `health_check` - Check server status (cache, config, and metrics)

### Reading Operations
- `read_slide_content` - Read comprehensive slide content (text, shapes, images, visibility)
- `read_slide_text` - Read all text content from a slide
- `read_slide_images` - Read image information from a slide
- `read_notes` - Read speaker notes from a slide
- `read_notes_batch` - Read notes from multiple slides efficiently

### Slide Manipulation
- `add_slide` - Add a new slide with specific layout
- `delete_slide` - Delete a slide from the presentation
- `duplicate_slide` - Duplicate an existing slide
- `change_slide_layout` - Change the layout of a slide
- `set_slide_visibility` - Hide or show a slide in the presentation

### Content Operations
- `update_slide_text` - Update text in a specific shape on a slide
- `replace_slide_image` - Replace an existing image on a slide
- `add_text_box` - Add a new text box to a slide
- `add_image` - Add a new image to a slide
- `replace_slide_content` - Replace all text content of a slide (clears existing text)
- `update_slide_content` - Update specific parts (title, specific shapes, or add new content)
- `replace_text` - Find and replace text in slide content or speaker notes (with regex support)

### Notes Operations
- `update_notes` - Update speaker notes (safe zip-based editing)
- `update_notes_batch` - Update multiple slides atomically
- `process_notes_workflow` - Complete workflow with validation and pre-processed content
- `format_notes_structure` - Format notes into structured short/original format

### LLM Tools (Azure AI Foundry)
- `summarize_text_llm` - Summarize text with optional `style` (`concise`/`detailed`/`bullet_points`) and `max_words`.
- `translate_text_llm` - Translate text to `target_lang` (optional `source_lang`, `preserve_terms`).
- `generate_slide_content_llm` - Generate `title+bullets`, `speaker_notes`, or `json` from `slide_content` or `pptx_path` + `slide_number`.

### Transcription Tools
- `transcribe_embedded_video_audio` - Transcribe audio from embedded videos in a PPTX. Supports `slide_numbers` or `slide_range`. Outputs results to a JSON file.

Example input:
```json
{
  "name": "generate_slide_content_llm",
  "arguments": {
    "pptx_path": "deck.pptx",
    "slide_number": 3,
    "output_format": "speaker_notes",
    "language": "Vietnamese"
  }
}
```

> LLM tools only appear when Foundry configuration is ready; check server logs if they are absent.

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

This is the recommended approach for processing multiple slides using MCP tools:

1. **Read notes in batch**: Use `read_notes_batch` with a `slide_range` (e.g., "1-20") to get content for multiple slides efficiently.
2. **Generate content**: For each slide with notes, generate the `short_text` and `original_text` in the required structure. Remember to **keep empty notes empty**.
3. **Apply atomically**: Use `process_notes_workflow` to apply all changes in a single operation. This is significantly faster and safer than updating slides one by one.

**Example Tool Call Sequence:**
- Call `read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")`
- (AI generates notes data for slides 1, 3, 5...)
- Call `process_notes_workflow(pptx_path="deck.pptx", notes_data=[...], in_place=true)`

### Single Slide Notes Update

For updating individual slides:

1. **Read single slide**: Use `read_notes` for the specific `slide_number`.
2. **Update with structure**: Call `update_notes` with the `notes_text` formatted as per the guidelines.

**Example Tool Call:**
- Call `update_notes(pptx_path="deck.pptx", slide_number=5, notes_text="- Short version:\n...\n\n- Original:\n...")`

### Embedded Video Transcription

For processing presentations with video content:

1. **Check for videos**: Use `transcribe_embedded_video_audio` with a `slide_range`. The tool will automatically discover videos.
2. **Review Transcripts**: The tool writes a JSON file (e.g., `deck.pptx.transcripts.json`) containing text for each video segment found.
3. **Incorporate into Notes**: Use the transcribed text to enrich or generate speaker notes for those slides.

**Example Tool Call:**
- Call `transcribe_embedded_video_audio(pptx_path="presentation.pptx", slide_range="1-5", language="en")`

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
- Status tracking files allow safe interruption and resume
- Always validate notes structure before applying updates

## Example Agent Instructions

When configuring your AI agent in VS Code, include these instructions:

```markdown
# PPTX Notes Processing Agent

You are an AI agent specialized in processing PowerPoint speaker notes using the PPTX MCP Server.

## Your Capabilities
- Read and analyze PPTX presentations
- Manipulate slides (add, delete, duplicate, change layout)
- Update slide content (text boxes, images)
- **Transcribe audio from embedded videos**
- Translate speaker notes to Vietnamese with proper tone
- Create short/original note versions
- Process multiple slides efficiently

## Your Guidelines
1. Always read notes in batch for multi-slide operations
2. Backup the original notes in a file called "original_notes.txt" store in `docs/backup` directory for further reference
3. Keep empty notes empty (don't invent content)
4. Use Vietnamese conversational style: "anh/chị", "chúng ta"
5. Provide both short (30-50%) and original (100%) versions
6. Never modify slide content, only speaker notes
7. Use batch operations for efficiency
8. Do not translate the technical terms.


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
- For LLM tools, ensure `AZURE_AI_PROJECT_ENDPOINT` and `MODEL_DEPLOYMENT_NAME` are set.
- For Transcription tools, ensure `SPEECH_KEY` and `SPEECH_ENDPOINT` (or `SPEECH_REGION`) are set.
- Check that `ffmpeg` is installed and in your PATH for transcription tools to work.

### File Access Issues
- Verify file paths are correct
- Check file permissions
- For Docker: ensure volumes are mounted correctly
- Verify MCP_WORKSPACE_DIRS includes your presentation directory

## Advanced Features

### Batch Operations Performance

Batch operations are 50-100x faster than individual operations. Always prefer `update_notes_batch` or `process_notes_workflow` over multiple calls to `update_notes`.

### Safe Zip-based Editing

The server uses zip-based editing for notes by default to preserve animations and transitions. When calling `update_notes` or `update_notes_batch`, you don't need to specify an engine; the server handles the safe editing automatically.

### Status Tracking for Long Operations

For large presentations, use `process_notes_workflow` with a `status_file` parameter. This allows the server to track progress and enables safe interruption and resumption of long-running operations.

## Best Practices

1. **Always use batch operations** for multiple slides
2. **Preserve empty notes** - don't fill them unless requested
3. **Create backups** before overwriting large presentations
4. **Use safe zip-based editing** for notes updates
5. **Transcribe video content** when slides have embedded media to provide better context
6. **Validate structure** before applying updates
7. **Log operations** for debugging and audit trails

### MUST
- run on .venv environment with all the python commands
```bash
source .venv/bin/activate &&<your python command>
```