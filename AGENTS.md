# Agent Instructions

## Project context

This repository is a **project for building automated processes for PPTX notes and more**. It includes tools and scripts for processing, translating, and managing PowerPoint speaker notes using Azure Foundry Models Response API.

The project includes:
- Automated PPTX speaker notes processing with translation and summarization
- Integration with Azure Foundry Models Response API for AI-powered note generation
- Utilities for reading, updating, and managing PPTX files
- Support for multi-language note processing (Vietnamese/English)
- **MCP Server**: Model Context Protocol server for PPTX manipulation via AI agents

Primary audience: Developers and content creators working with PowerPoint presentations.

## What to generate

- Focus on building and improving automated PPTX processing tools and scripts.
- When working with speaker notes, they should be written in **Vietnamese** (or target language), using a **casual, conversational** tone suitable for a live presentation.
- Extend and improve the automation capabilities of the project.

## Pronouns and voice (very important)

- Address the audience as **"anh/chị"**.
- Use **"chúng ta"** when referring to shared actions/goals.
- Avoid overly formal or academic phrasing.

## Style guidelines

- Keep sentences short and speakable.
- Use simple bullet points; avoid long paragraphs unless explicitly requested.
- Don’t invent new product claims or numbers. If citing stats, keep the provided values and add a short “Nguồn:” line when available.- Default to comprehensive speaker notes that fully explain concepts. However, when the user explicitly requests brevity (e.g., "ngắn gọn thôi", "keep it short"), reduce length significantly while preserving all key points.
## Transitions between slides

- Do **not** write a transition phrase that references the *next* slide (e.g., “phần tiếp theo…”, “sang slide sau…”) until the user has already inserted/provided the next slide content.
- If needed, end the current slide with a neutral wrap-up sentence that stands on its own.

## Scope constraints

- Do not add new pages/sections/slides unless the user explicitly asks.
- Keep changes minimal and aligned with the existing structure.

## PPTX Speaker Notes

> **⚠️ IMPORTANT:** Use **MCP Server tools** instead of direct script usage. The scripts are deprecated. See [MIGRATION.md](MIGRATION.md) for migration instructions.

When the user asks to translate or edit speaker notes inside a `.pptx`:

- **Preferred:** Use MCP server `notes_tools` for all operations:
  - `read_notes` / `read_notes_batch` - Read speaker notes
  - `update_notes` / `update_notes_batch` - Update speaker notes
  - `process_notes_workflow` - Automated processing with Azure Foundry Models
- **Benefits of MCP tools:**
  - Safe editing that preserves slide structure, animations, and transitions
  - Input validation and security checks
  - Structured error handling
  - Automatic logging and monitoring
  - Type safety
- Never change slide content or layout; only change speaker notes. If a slide note is empty, keep it empty.
- Use Vietnamese speaker note style per this file: address as "anh/chị", use "chúng ta", keep sentences short and speakable.

### Automated Note Processing with MCP Tools

The MCP server provides `process_notes_workflow` tool which uses Azure Foundry Models Response API to automatically:

1. **Long Version Creation (`create_long_version`)**:
   - Detects the language of input notes (Vietnamese or English)
   - Translates English notes to Vietnamese (or vice versa) if needed
   - Skips translation if notes are already in the target language
   - Uses Azure Foundry Models Response API for high-quality translation
   - Maintains conversational, speakable tone suitable for presentations

2. **Short Version Creation (`create_short_version`)**:
   - Generates concise summaries (30-50% of original length)
   - Preserves key points and main ideas
   - Maintains conversational tone
   - Works with any input language, outputs in target language (default: Vietnamese)
   - Uses Azure Foundry Models Response API for intelligent summarization

3. **Automated Workflow**:
   - Processes JSON dumps of PPTX notes
   - Automatically extracts original text if notes are already formatted
   - Generates both short and long versions for each slide
   - Can automatically update PPTX files after processing
   - Processes slides in parallel batches for improved performance
   - Tracks progress in status file for resume capability

4. **Parallel Processing & Status Tracking**:
   - Processes multiple slides concurrently (configurable batch size)
   - Creates status tracking file (`.status.json`) with per-slide status
   - Supports resume mode to continue from interruptions
   - Thread-safe status updates during parallel processing
   - Dry-run mode for testing without API calls

### Note Format: Long and Short Versions

When translating or creating speaker notes for slides:

1. **Always provide TWO versions** of each note:
  - **Short version**: Brief, condensed summary derived from the original version (typically 30-50% of the original length)
  - **Original version**: Full, comprehensive translation/explanation in the target language

2. **Format template** for each slide's notes:
   ```
  - Short version:
  [Brief summary covering only key points]
  
  - Original:
  [Full translation/explanation with all details, examples, and explanations]
   ```

3. **Content guidelines**:
  - Short version: Extract only the most critical points, suitable for quick reference during presentation
  - Original version: Translate all content, maintaining full context and detail
  - Both versions must use "anh/chị" and "chúng ta" pronouns (if Vietnamese)
  - Both versions must be in conversational, speakable language

4. **Workflow**:
   - **Automated (Recommended)**: Use MCP server `process_notes_workflow` tool
     - Integrated security and validation
     - Automatic parallel processing
     - Structured error handling and logging
     - See [MIGRATION.md](MIGRATION.md) for details
   - **Legacy (Deprecated)**: `scripts/update_notes_format.py` - will be removed
   - **Manual**: When updating notes manually via MCP tools:
     - Use `read_notes_batch` to dump current notes
     - Create JSON with long/short versions for target slides
     - Use `update_notes_batch` to apply changes
     - Review formatted notes before applying

### Commands

> **⚠️ DEPRECATION WARNING:** Direct script usage is deprecated. Use MCP server tools instead. See [MIGRATION.md](MIGRATION.md).

**MCP Server Setup (Recommended):**
- Always use `source .venv/bin/activate` to activate the virtual environment
- Setup (one-time):
	- `python3 -m venv .venv`
	- `source .venv/bin/activate`
	- `pip3 install -r requirements.txt`
	- Set environment variables:
	  - `AZURE_AI_PROJECT_ENDPOINT`: Your Azure AI Project endpoint
	  - `MODEL_DEPLOYMENT_NAME`: Your model deployment name

**Using MCP Tools (Recommended):**
- See [MIGRATION.md](MIGRATION.md) for complete MCP tool usage examples
- Use `read_notes_batch` instead of `pptx_notes.py dump`
- Use `update_notes_batch` instead of `pptx_notes.py apply`
- Use `process_notes_workflow` instead of `update_notes_format.py`

**Legacy CLI Scripts (Deprecated - Will Show Warnings):**
- Dump notes to JSON (use `read_notes_batch` instead):
	- `python3 scripts/pptx_notes.py dump "path/to/deck.pptx"`

- Process notes (use `process_notes_workflow` instead):
	- `python3 scripts/update_notes_format.py --input "path/to/notes.json" --pptx "path/to/deck.pptx" --output-language vietnamese`

- Apply updates manually (use `update_notes_batch` instead):
	- `python3 scripts/pptx_notes.py apply "path/to/deck.pptx" "path/to/updates.json" --in-place --engine zip`

### Update format

- Updates file should follow this structure:
  ```json
  {
    "slides": [
      {
        "slide": 63,
        "notes": "- short version:\n[brief content]\n\n- original:\n[full content]"
      }
    ]
  }
  ```

### Safety

- Before overwriting in-place, create a backup copy of the PPTX (especially for large decks).
- Status tracking file allows safe interruption and resume of processing.
- Use `--dry-run` to test processing logic before running with actual API calls.

## MCP Server

The project includes a **Model Context Protocol (MCP) server** that exposes PPTX manipulation capabilities as tools and resources, allowing AI agents to interact with PowerPoint files through natural language commands.

### Architecture

The MCP server follows a **separation of concerns** approach:

- **MCP Server Responsibilities**:
  - PPTX file manipulation (read, write, edit)
  - Safe file operations (backup, validation)
  - Structure operations (formatting, layout)
  - **NOT** content generation (translation, summarization, AI processing)

- **AI Agent Responsibilities**:
  - Content generation using LLM
  - Translation and summarization
  - Language detection
  - Natural language understanding
  - Orchestrating multiple MCP tool calls

### Available Tools

#### Read Tools
- `read_slide_content`: Read comprehensive content from a slide (text, shapes, images)
- `read_slide_text`: Read all text content from a slide
- `read_slide_images`: Read image information from a slide
- `read_presentation_info`: Get presentation metadata (slide count, dimensions)

#### Edit Tools
- `update_slide_text`: Update text in a specific shape on a slide
- `replace_slide_image`: Replace an existing image on a slide
- `add_text_box`: Add a new text box to a slide
- `add_image`: Add a new image to a slide

#### Slide Management Tools
- `add_slide`: Add a new slide to the presentation
- `delete_slide`: Delete a slide from the presentation
- `duplicate_slide`: Duplicate a slide
- `change_slide_layout`: Change the layout of a slide

#### Notes Tools
- `read_notes`: Read speaker notes from slide(s)
- `read_notes_batch`: **NEW** - Read speaker notes from multiple slides at once (efficient batch operation)
- `update_notes`: Update speaker notes using safe zip-based editing (preserves animations/transitions)
- `update_notes_batch`: **NEW** - Update notes for multiple slides atomically (all succeed or all fail)
- `format_notes_structure`: Format notes text into structured format (short/original template)
- `process_notes_workflow`: **NEW** - Complete workflow: validate, format, and apply pre-processed notes to multiple slides atomically

**Batch Operation Benefits:**
- Faster execution (fewer round-trips between agent and server)
- Atomic updates (all succeed or all fail)
- Built-in validation and error handling
- Automatic formatting (for `process_notes_workflow`)
- Recommended for multi-slide operations

### Resources

The MCP server exposes PPTX files as resources, allowing AI agents to discover and access presentations:
- Resources are automatically discovered in common locations (`src/deck`, `src`, current directory)
- Each resource provides metadata (file path, slide count, dimensions)

### Usage

#### Running the MCP Server

**Local execution:**
```bash
python3 -m mcp_server.server
```

**Docker execution:**
```bash
# Build image
docker build -f docker/Dockerfile -t pptx-mcp-server:latest .

# Run container
docker run -it --rm \
  -v $(pwd)/src/deck:/data/pptx:rw \
  pptx-mcp-server:latest
```

**Docker Compose:**
```bash
docker-compose -f docker/docker-compose.yml up
```

#### Integration with AI Agents

Configure the MCP server in your AI agent's MCP settings:

```json
{
  "mcpServers": {
    "pptx": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "env": {}
    }
  }
}
```

Or with Docker:
```json
{
  "mcpServers": {
    "pptx": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-v", "/path/to/pptx:/data/pptx:rw",
        "pptx-mcp-server:latest"
      ]
    }
  }
}
```

### Workflow Example: Notes Processing with AI Agent

#### Single Slide Processing (Legacy Method)

1. **AI Agent calls**: `read_notes(pptx_path, slide_number=1)`
2. **AI Agent uses its LLM to**:
   - Detect language
   - Translate if needed
   - Generate short version (30-50% length)
   - Generate full version
3. **AI Agent calls**: `format_notes_structure(short_text, original_text, format_type="short_original")`
4. **AI Agent calls**: `update_notes(pptx_path, slide_number=1, notes_text=formatted_text, in_place=True)`

#### Batch Processing (RECOMMENDED for Multiple Slides)

**Example: Translate slides 1-20 from English to Vietnamese**

```python
# 1. Read all notes at once
notes = read_notes_batch(pptx_path="deck.pptx", slide_range="1-20")

# 2. AI Agent processes with LLM
notes_data = []
for slide in notes["slides"]:
    # LLM detects language, translates, summarizes
    lang = llm.detect_language(slide["notes"])
    translated = llm.translate(slide["notes"], target="vietnamese") if lang == "english" else slide["notes"]
    short = llm.summarize(translated, max_length_percent=40)
    
    notes_data.append({
        "slide_number": slide["slide_number"],
        "short_text": short,
        "original_text": translated
    })

# 3. Apply all changes atomically with automatic formatting
result = process_notes_workflow(
    pptx_path="deck.pptx",
    notes_data=notes_data,
    in_place=True
)
# Result: All 20 slides updated in one atomic operation
```

**Benefits of Batch Processing:**
- 🚀 **Faster**: Single read + single write vs 20 reads + 20 writes
- 🔒 **Atomic**: All updates succeed or all fail (no partial updates)
- ✅ **Automatic formatting**: `process_notes_workflow` handles formatting
- 🎯 **Better error handling**: Clear validation and error messages
- 📊 **Progress tracking**: Know exactly what succeeded/failed

### Key Features

1. **Safe Editing**: Default to zip/XML-based editing to preserve animations and transitions
2. **Comprehensive Operations**: Support all major PPTX operations
3. **Error Handling**: Robust validation and error messages
4. **Separation of Concerns**: MCP server handles PPTX operations only; AI agent handles content generation
5. **Resource Support**: PPTX files exposed as MCP resources for discovery

### Notes on Content Generation

- The MCP server does **NOT** include Azure dependencies or content generation logic
- Content generation (translation, summarization) should be handled by the calling AI agent using its LLM capabilities
- The existing `scripts/update_notes_format.py` remains available for CLI/batch processing with Azure integration
- This separation allows the MCP server to be used with any LLM provider (OpenAI, Anthropic, Azure, local models)

### Safety Considerations

- The MCP server uses safe zip-based editing for notes updates (preserves animations/transitions)
- Edit operations create new files by default (use `in_place` parameter for in-place updates)
- Always validate slide numbers and file paths before operations
- Consider creating backups before in-place modifications
