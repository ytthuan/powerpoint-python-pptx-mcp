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

#### `read_notes_batch`

**NEW:** Read speaker notes from multiple slides at once for efficient batch processing.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_numbers` (optional): Array of slide numbers (1-indexed), e.g., `[1, 5, 12, 20]`
- `slide_range` (optional): Slide range string like `"1-10"` (alternative to `slide_numbers`)

**Important:** Provide either `slide_numbers` OR `slide_range`, not both. If both are provided, an error will be returned.

**Returns:**
```json
{
  "success": true,
  "pptx_path": "path/to/file.pptx",
  "total_slides": 10,
  "slides": [
    {
      "slide_number": 1,
      "notes": "Speaker notes for slide 1"
    },
    {
      "slide_number": 2,
      "notes": "Speaker notes for slide 2"
    }
  ]
}
```

**Usage Examples:**
- Read specific slides: `read_notes_batch(pptx_path="deck.pptx", slide_numbers=[1, 5, 12])`
- Read range: `read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")`
- Read all slides: `read_notes_batch(pptx_path="deck.pptx")`

#### `update_notes_batch`

**NEW:** Update speaker notes for multiple slides atomically using safe zip-based editing. All updates succeed or all fail (atomic operation).

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `updates` (required): Array of update objects, each with:
  - `slide_number` (integer): Slide number (1-indexed)
  - `notes_text` (string): New notes text content
- `in_place` (optional): Update file in-place (default: `true` for batch operations)
- `output_path` (optional): Output PPTX path (only used if `in_place` is `false`)

**Returns:**
```json
{
  "success": true,
  "pptx_path": "path/to/file.pptx",
  "updated_slides": 5,
  "in_place": true,
  "slides": [1, 3, 5, 7, 9]
}
```

**Important Notes:**
- **Atomic operation**: All updates succeed or all fail (rollback on error)
- Uses safe zip-based editing that preserves animations and transitions
- More efficient than calling `update_notes` multiple times
- Default is `in_place=true` for batch operations

**Usage Example:**
```python
updates = [
    {"slide_number": 1, "notes_text": "Updated notes for slide 1"},
    {"slide_number": 3, "notes_text": "Updated notes for slide 3"},
    {"slide_number": 5, "notes_text": "Updated notes for slide 5"}
]
result = update_notes_batch(pptx_path="deck.pptx", updates=updates, in_place=True)
```

#### `process_notes_workflow`

**NEW:** Orchestrate complete notes processing workflow - validate, format, and apply pre-processed notes to multiple slides atomically. AI agent provides already-processed content.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `notes_data` (required): Array of pre-processed notes, each with:
  - `slide_number` (integer): Slide number (1-indexed)
  - `short_text` (string): Short version text (AI-generated)
  - `original_text` (string): Original/full version text (AI-generated)
- `in_place` (optional): Update file in-place (default: `true`)
- `output_path` (optional): Output PPTX path (only used if `in_place` is `false`)

**Returns:**
```json
{
  "success": true,
  "workflow": "process_notes_workflow",
  "pptx_path": "path/to/file.pptx",
  "formatted_slides": 10,
  "updated_slides": 10,
  "in_place": true,
  "slides": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
}
```

**What This Tool Does:**
1. Validates all input data (slide numbers, text content)
2. Formats each note using the "short/original" structure
3. Applies all updates atomically to the PPTX file
4. Returns detailed status report

**Usage Pattern:**
```python
# 1. Agent reads notes
notes = read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")

# 2. Agent processes with LLM (translation, summarization)
notes_data = []
for note in notes["slides"]:
    short = llm.summarize(note["notes"])
    translated = llm.translate(note["notes"], target="vietnamese")
    notes_data.append({
        "slide_number": note["slide_number"],
        "short_text": short,
        "original_text": translated
    })

# 3. Apply all changes atomically with formatting
result = process_notes_workflow(
    pptx_path="deck.pptx",
    notes_data=notes_data,
    in_place=True
)
```

**Benefits:**
- Single call handles validation, formatting, and updates
- Atomic operation: all succeed or all fail
- Clear error messages for debugging
- Reduces round-trips between agent and MCP server

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

### Workflow 2: Batch Process Multiple Slides (Legacy Method)

**Goal:** Process notes for multiple slides using individual calls.

**Steps:**
1. Read presentation info: `read_presentation_info(pptx_path)` to get slide count
2. For each slide:
   - Read notes: `read_notes(pptx_path, slide_number)`
   - Process with LLM (translate, summarize, etc.)
   - Format: `format_notes_structure(short, original)`
   - Update: `update_notes(pptx_path, slide_number, formatted, in_place=True)`

**Note:** This method works but requires multiple round-trips. See Workflow 3 for efficient batch processing.

### Workflow 3: Efficient Batch Translation (RECOMMENDED)

**Goal:** Translate and update speaker notes for multiple slides efficiently using batch operations.

**Steps:**

```python
# 1. Read notes from multiple slides at once
result = read_notes_batch(
    pptx_path="presentation.pptx",
    slide_range="1-10"  # or slide_numbers=[1, 5, 12, 20]
)

# 2. Process all notes with LLM
notes_data = []
for slide in result["slides"]:
    # Detect language (using your LLM)
    detected_lang = llm.detect_language(slide["notes"])
    
    # Generate translation (using your LLM)
    if detected_lang == "english":
        translated = llm.translate(slide["notes"], target="vietnamese")
    else:
        translated = slide["notes"]
    
    # Generate short version (using your LLM)
    short = llm.summarize(translated, max_length_percent=40)
    
    notes_data.append({
        "slide_number": slide["slide_number"],
        "short_text": short,
        "original_text": translated
    })

# 3. Apply all changes atomically with automatic formatting
result = process_notes_workflow(
    pptx_path="presentation.pptx",
    notes_data=notes_data,
    in_place=True
)

print(f"Updated {result['updated_slides']} slides successfully!")
```

**Benefits:**
- **Single read operation** for all slides
- **Single update operation** applies all changes atomically
- **Automatic formatting** of notes structure
- **Built-in validation** and error handling
- **Rollback on failure** - all succeed or all fail

### Workflow 4: Batch Update with Custom Processing

**Goal:** Update multiple slides with custom logic using `update_notes_batch`.

**Steps:**

```python
# 1. Read notes
notes = read_notes_batch(pptx_path="deck.pptx", slide_numbers=[1, 3, 5, 7])

# 2. Process with custom logic
updates = []
for slide in notes["slides"]:
    # Custom processing per slide
    processed_text = custom_process(slide["notes"])
    
    # Format manually if needed
    formatted = format_notes_structure(
        short_text=extract_summary(processed_text),
        original_text=processed_text
    )
    
    updates.append({
        "slide_number": slide["slide_number"],
        "notes_text": formatted["formatted_text"]
    })

# 3. Apply all updates atomically
result = update_notes_batch(
    pptx_path="deck.pptx",
    updates=updates,
    in_place=True
)
```

**When to use:**
- Need more control over formatting
- Custom processing logic per slide
- Want to manually call `format_notes_structure`

---

## Best Practices

### 1. Always Read Before Writing

Before updating notes or content, always read the current state.

### 2. Validate Slide Numbers

Always check slide count before operations.

### 3. Use Batch Operations for Multiple Slides

**RECOMMENDED:** When processing multiple slides, use batch operations:
- `read_notes_batch` instead of multiple `read_notes` calls
- `update_notes_batch` or `process_notes_workflow` instead of multiple `update_notes` calls

**Benefits:**
- Faster execution (fewer round-trips)
- Atomic updates (all succeed or all fail)
- Built-in validation
- Better error handling

### 4. Use In-Place Updates Carefully

- **For notes:** Safe to use `in_place=True` (uses zip-based editing)
- **For slide content:** Consider using `output_path` to create new file first
- **Always backup** important files before in-place updates

### 5. Handle Errors Gracefully

- Check if files exist
- Validate slide numbers
- Provide clear error messages to users
- Suggest alternatives when operations fail
- For batch operations, check the `success` field in results

### 6. Provide Progress Updates

For batch operations, inform the user about progress:
- Show which slides are being processed
- Report results after completion
- Indicate any failures clearly

### 7. Format Notes Properly

Always use `format_notes_structure` or `process_notes_workflow` to ensure consistent format.

### 8. Choose the Right Tool

- **Single slide**: Use `read_notes` and `update_notes`
- **Multiple slides with LLM processing**: Use `read_notes_batch` + `process_notes_workflow`
- **Multiple slides with custom formatting**: Use `read_notes_batch` + `update_notes_batch`
- **Simple formatting only**: Use `format_notes_structure`

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

### Example 4: Complete Batch Translation Workflow

**User Request:** "Translate speaker notes for slides 1-20 from English to Vietnamese"

**Agent Actions:**

```python
# Step 1: Read all notes at once
notes_result = read_notes_batch(
    pptx_path="presentation.pptx",
    slide_range="1-20"
)

print(f"Read {notes_result['total_slides']} slides")

# Step 2: Process all notes with LLM
notes_data = []
for slide in notes_result["slides"]:
    slide_num = slide["slide_number"]
    original_notes = slide["notes"]
    
    # LLM: Detect language
    lang = llm.detect_language(original_notes)
    
    # LLM: Translate if needed
    if lang == "english":
        vietnamese_text = llm.translate(
            text=original_notes,
            target_language="vietnamese",
            style="conversational",
            pronouns={"audience": "anh/chị", "we": "chúng ta"}
        )
    else:
        vietnamese_text = original_notes
    
    # LLM: Generate short version (30-40% length)
    short_text = llm.summarize(
        text=vietnamese_text,
        target_length_percent=35,
        preserve_key_points=True
    )
    
    notes_data.append({
        "slide_number": slide_num,
        "short_text": short_text,
        "original_text": vietnamese_text
    })
    
    print(f"Processed slide {slide_num}/20")

# Step 3: Apply all changes atomically
result = process_notes_workflow(
    pptx_path="presentation.pptx",
    notes_data=notes_data,
    in_place=True
)

if result["success"]:
    print(f"✅ Successfully updated {result['updated_slides']} slides!")
    print(f"All notes now have Vietnamese translations with short summaries.")
else:
    print(f"❌ Error: {result.get('error', 'Unknown error')}")
```

**Key Points:**
- Single `read_notes_batch` call reads all 20 slides
- LLM processes each slide's notes (translation + summarization)
- Single `process_notes_workflow` call applies all changes atomically
- Automatic formatting with "- Short version:" and "- Original:" structure
- Progress feedback to user throughout

### Example 5: Error Handling in Batch Operations

**User Request:** "Update notes for slides 5, 15, and 100"

**Agent Actions:**

```python
# Attempt batch update
try:
    # First, validate slide count
    info = read_presentation_info("presentation.pptx")
    max_slides = info["slide_count"]  # e.g., 50
    
    slide_numbers = [5, 15, 100]
    
    # Check if all slides are valid
    invalid_slides = [s for s in slide_numbers if s > max_slides]
    
    if invalid_slides:
        print(f"❌ Error: Invalid slide numbers: {invalid_slides}")
        print(f"Presentation has only {max_slides} slides.")
        print(f"Valid range: 1-{max_slides}")
        return
    
    # Proceed with batch read
    notes = read_notes_batch(
        pptx_path="presentation.pptx",
        slide_numbers=slide_numbers
    )
    
    # ... process and update ...
    
except Exception as e:
    print(f"❌ Error processing notes: {str(e)}")
    print("Please check the file path and slide numbers.")
```

**Key Points:**
- Always validate inputs before batch operations
- Check slide count before reading/updating
- Provide clear error messages
- Suggest valid ranges to user

---

## Summary

- **MCP Server** = File operations (read, write, edit PPTX)
- **AI Agent** = Content generation (translate, summarize, analyze)
- **Use batch operations** for multiple slides (more efficient)
- **Always** read before writing
- **Always** format notes structure before updating (or use `process_notes_workflow`)
- **Always** validate inputs (slide numbers, file paths)
- **Follow** Vietnamese speaker notes guidelines when generating content
- **Provide** progress updates for batch operations
- **Handle** errors gracefully with clear messages

### Quick Reference: Tool Selection

| Task | Recommended Tool |
|------|-----------------|
| Read single slide notes | `read_notes` |
| Read multiple slides notes | `read_notes_batch` |
| Update single slide notes | `update_notes` |
| Update multiple slides notes | `update_notes_batch` |
| Complete workflow with formatting | `process_notes_workflow` |
| Format notes structure only | `format_notes_structure` |
| Get presentation info | `read_presentation_info` |

For more details on specific tools, refer to the tool schemas available through the MCP protocol.


