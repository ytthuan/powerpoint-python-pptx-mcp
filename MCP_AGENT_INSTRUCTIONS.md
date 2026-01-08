# MCP Server Agent Instructions

This document provides comprehensive instructions for AI agents working with the PPTX MCP Server.

## Table of Contents

1. [Architecture & Separation of Concerns](#architecture--separation-of-concerns)
2. [Available Tools Reference](#available-tools-reference)
3. [Resources](#resources)
4. [Common Workflows](#common-workflows)
5. [Best Practices](#best-practices)
6. [Error Handling](#error-handling)
7. [Vietnamese Speaker Notes Guidelines](#vietnamese-speaker-notes-guidelines)
8. [Examples](#examples)

---

## Architecture & Separation of Concerns

### MCP Server Responsibilities

The MCP server handles **PPTX file operations only**:

- ✅ Reading PPTX content (slides, text, images, notes)
- ✅ Writing/updating PPTX files (safe zip-based editing for notes)
- ✅ Slide management (add, delete, duplicate, layout changes)
- ✅ Content editing (text, images, shapes)
- ✅ File validation and error handling
- ❌ **NOT** content generation (translation, summarization, AI processing)
- ❌ **NOT** language detection
- ❌ **NOT** text formatting beyond structure templates

### AI Agent Responsibilities

The AI agent (you) handles **content generation and intelligence**:

- ✅ Content generation using LLM capabilities
- ✅ Translation between languages
- ✅ Summarization and content condensation
- ✅ Language detection
- ✅ Natural language understanding
- ✅ Orchestrating multiple MCP tool calls
- ✅ Decision-making about what operations to perform

### Why This Separation?

- **Flexibility**: MCP server works with any LLM provider (OpenAI, Anthropic, Azure, local models)
- **Maintainability**: Clear boundaries between file operations and AI logic
- **Safety**: File operations are validated and safe; AI handles creative/content tasks
- **Reusability**: MCP server can be used by different AI agents with different capabilities

---

## Available Tools Reference

### Read Tools

#### `read_slide_content`

Read comprehensive content from a slide including text, shapes, and images.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (optional): Slide number (1-indexed). If omitted, returns all slides.

**Returns:**
```json
{
  "slide_number": 1,
  "text": "Slide text content",
  "shapes": [
    {
      "shape_id": 2,
      "type": "TEXT_BOX",
      "text": "Shape text"
    }
  ],
  "images": [...]
}
```

#### `read_slide_text`

Read all text content from a slide (simpler than `read_slide_content`).

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (required): Slide number (1-indexed)

#### `read_slide_images`

Get image information from a slide.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (required): Slide number (1-indexed)

#### `read_presentation_info`

Get presentation metadata.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file

**Returns:**
```json
{
  "slide_count": 50,
  "slide_size": {
    "width": 10.0,
    "height": 7.5
  }
}
```

### Notes Tools

#### `read_notes`

Read speaker notes from slide(s).

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (optional): Slide number (1-indexed). If omitted, returns all slides.

#### `update_notes`

Update speaker notes using safe zip-based editing (preserves animations/transitions).

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (required): Slide number (1-indexed)
- `notes_text` (required): New notes text content
- `in_place` (optional): Update file in-place (default: `false`, creates new file)
- `output_path` (optional): Output PPTX path (required if `in_place` is `false`)

**Important Notes:**
- Uses safe zip-based editing that preserves animations and transitions
- When `in_place=true`, the original file is updated (backup recommended)
- When `in_place=false`, a new file is created

#### `format_notes_structure`

Format notes text into structured format (short/original template). **Does NOT generate content**, only formats structure.

**Parameters:**
- `short_text` (required): Short version text
- `original_text` (required): Original/full version text
- `format_type` (optional): Format type - `"short_original"` (default) or `"simple"`

**Usage Pattern:**
1. Agent generates `short_text` and `original_text` using LLM
2. Agent calls `format_notes_structure` to format them
3. Agent calls `update_notes` with the formatted text

### Edit Tools

#### `update_slide_text`

Update text in a specific shape on a slide.

**Note:** This uses `python-pptx` which rewrites the entire PPTX. Use with caution on complex presentations.

#### `replace_slide_image`

Replace an existing image on a slide.

#### `add_text_box`

Add a new text box to a slide.

#### `add_image`

Add a new image to a slide.

### Slide Management Tools

#### `add_slide`

Add a new slide to the presentation.

#### `delete_slide`

Delete a slide from the presentation.

#### `duplicate_slide`

Duplicate a slide.

#### `change_slide_layout`

Change the layout of a slide.

---

## Common Workflows

### Workflow 1: Translate and Update Speaker Notes

**Goal:** Translate speaker notes from English to Vietnamese and update the PPTX.

**Steps:**
1. Read notes from a slide: `read_notes(pptx_path, slide_number)`
2. Detect language (using your LLM)
3. Generate Vietnamese translation (using your LLM)
4. Generate short version (30-50% length, using your LLM)
5. Format structure: `format_notes_structure(short_text, original_text)`
6. Update notes: `update_notes(pptx_path, slide_number, formatted_text, in_place=True)`

### Workflow 2: Batch Process Multiple Slides

**Goal:** Process notes for multiple slides.

**Steps:**
1. Read presentation info: `read_presentation_info(pptx_path)` to get slide count
2. For each slide:
   - Read notes: `read_notes(pptx_path, slide_number)`
   - Process with LLM (translate, summarize, etc.)
   - Format: `format_notes_structure(short, original)`
   - Update: `update_notes(pptx_path, slide_number, formatted, in_place=True)`

---

## Best Practices

### 1. Always Read Before Writing

Before updating notes or content, always read the current state.

### 2. Validate Slide Numbers

Always check slide count before operations.

### 3. Use In-Place Updates Carefully

- **For notes:** Safe to use `in_place=True` (uses zip-based editing)
- **For slide content:** Consider using `output_path` to create new file first
- **Always backup** important files before in-place updates

### 4. Handle Errors Gracefully

- Check if files exist
- Validate slide numbers
- Provide clear error messages to users
- Suggest alternatives when operations fail

### 5. Provide Progress Updates

For batch operations, inform the user about progress.

### 6. Format Notes Properly

Always use `format_notes_structure` before updating notes to ensure consistent format.

---

## Vietnamese Speaker Notes Guidelines

When generating Vietnamese speaker notes, follow these guidelines:

### Pronouns and Voice

- **Address audience as "anh/chị"** (not "bạn" or "quý vị")
- **Use "chúng ta"** when referring to shared actions/goals
- **Avoid overly formal or academic phrasing**
- **Keep conversational and speakable**

### Style Guidelines

- **Keep sentences short and speakable**
- **Use simple bullet points**; avoid long paragraphs
- **Don't invent product claims or numbers**
- **If citing stats, add "Nguồn:" when available**

### Note Format

Always provide **TWO versions**:

1. **Short version** (30-50% of original length)
2. **Original version** (full content)

### Format Template

```
- Short version:
[Brief summary covering only key points]

- Original:
[Full translation/explanation with all details, examples, and explanations]
```

---

## Examples

### Example 1: Simple Note Translation

**User Request:** "Translate the notes on slide 3 to Vietnamese"

**Agent Actions:**
1. `read_notes("presentation.pptx", 3)`
2. [LLM detects English, generates Vietnamese]
3. [LLM generates short version]
4. `format_notes_structure(short_vn, full_vn)`
5. `update_notes("presentation.pptx", 3, formatted, in_place=True)`

### Example 2: Batch Processing

**User Request:** "Translate all notes in the presentation to Vietnamese"

**Agent Actions:**
1. `read_presentation_info("presentation.pptx")` → 50 slides
2. `read_notes("presentation.pptx")` → All notes
3. [For each slide: LLM processes, formats, updates]
4. Progress updates: "Processing slide 10/50..."

---

## Summary

- **MCP Server** = File operations (read, write, edit PPTX)
- **AI Agent** = Content generation (translate, summarize, analyze)
- **Always** read before writing
- **Always** format notes structure before updating
- **Always** validate inputs (slide numbers, file paths)
- **Follow** Vietnamese speaker notes guidelines when generating content
- **Provide** progress updates for batch operations
- **Handle** errors gracefully with clear messages

For more details on specific tools, refer to the tool schemas available through the MCP protocol.

