# Batch Operations for MCP Server

This document provides an overview of the batch operations added to the MCP server for efficient multi-slide speaker notes processing.

## Overview

Batch operations enable efficient processing of multiple slides in a single request, reducing round-trips between the AI agent and MCP server while maintaining atomic transactions (all succeed or all fail).

## New Tools

### 1. `read_notes_batch`

Read speaker notes from multiple slides at once.

**Parameters:**
- `pptx_path` (string, required): Path to the PPTX file
- `slide_numbers` (array, optional): Array of slide numbers, e.g., `[1, 5, 12, 20]`
- `slide_range` (string, optional): Slide range string, e.g., `"1-10"`

**Example:**
```python
# Read specific slides
result = read_notes_batch(pptx_path="deck.pptx", slide_numbers=[1, 3, 5])

# Read range
result = read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")

# Read all slides
result = read_notes_batch(pptx_path="deck.pptx")
```

### 2. `update_notes_batch`

Update speaker notes for multiple slides atomically.

**Parameters:**
- `pptx_path` (string, required): Path to the PPTX file
- `updates` (array, required): Array of update objects with `slide_number` and `notes_text`
- `in_place` (boolean, optional): Update file in-place (default: true)
- `output_path` (string, optional): Output path for new file

**Example:**
```python
updates = [
    {"slide_number": 1, "notes_text": "Updated notes for slide 1"},
    {"slide_number": 3, "notes_text": "Updated notes for slide 3"},
]
result = update_notes_batch(pptx_path="deck.pptx", updates=updates, in_place=True)
```

### 3. `process_notes_workflow`

Complete workflow that validates, formats, and applies pre-processed notes atomically.

**Parameters:**
- `pptx_path` (string, required): Path to the PPTX file
- `notes_data` (array, required): Array of notes with `slide_number`, `short_text`, and `original_text`
- `in_place` (boolean, optional): Update file in-place (default: true)
- `output_path` (string, optional): Output path for new file

**Example:**
```python
notes_data = [
    {
        "slide_number": 1,
        "short_text": "Brief summary",
        "original_text": "Full detailed notes"
    },
    {
        "slide_number": 2,
        "short_text": "Another summary",
        "original_text": "More detailed notes"
    }
]
result = process_notes_workflow(
    pptx_path="deck.pptx",
    notes_data=notes_data,
    in_place=True
)
```

## Complete Workflow Example

Here's a complete example of translating slides from English to Vietnamese:

```python
# 1. Read notes from multiple slides
notes = read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")

# 2. Process with LLM (this is done by the AI agent, not the MCP server)
notes_data = []
for slide in notes["slides"]:
    # LLM detects language, translates, and summarizes
    lang = llm.detect_language(slide["notes"])
    translated = llm.translate(slide["notes"], target="vietnamese")
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

print(f"Updated {result['updated_slides']} slides successfully!")
```

## Benefits

### Performance
- **Faster execution**: Single read + single write vs multiple round-trips
- **Reduced latency**: Fewer network/IPC calls between agent and server
- **Parallel processing**: Server can optimize internal operations

### Reliability
- **Atomic transactions**: All updates succeed or all fail (no partial updates)
- **Built-in validation**: Comprehensive input validation before processing
- **Clear error messages**: Detailed information about what failed and why

### Developer Experience
- **Automatic formatting**: `process_notes_workflow` handles formatting automatically
- **Progress tracking**: Know exactly which slides succeeded/failed
- **Type-safe**: Well-defined schemas for all parameters

## Architecture

The batch operations maintain the MCP server's separation of concerns:

- **MCP Server Responsibilities**:
  - Reading/writing PPTX files
  - Validating inputs (slide numbers, file paths)
  - Formatting note structures
  - Safe zip-based editing (preserves animations/transitions)
  
- **AI Agent Responsibilities**:
  - Content generation (translation, summarization)
  - Language detection
  - Natural language understanding
  - Orchestrating tool calls

## Testing

The implementation includes comprehensive unit tests:

- 7 tests for slide range parsing
- 6 tests for slide number validation
- 7 tests for batch update validation
- 7 integration tests with actual PPTX files
- **Total: 27 tests, all passing**

Run tests:
```bash
python3 -m pytest test_batch_operations.py -v
```

## Demonstration

Run the demonstration script to see batch operations in action:

```bash
python3 demo_batch_operations.py
```

The demo shows:
1. Reading notes from multiple slides
2. Updating notes for multiple slides atomically
3. Complete workflow with automatic formatting

## Migration Guide

### From Single-Slide Operations

**Before:**
```python
# Read each slide individually
for slide_num in range(1, 11):
    notes = read_notes(pptx_path="deck.pptx", slide_number=slide_num)
    # Process...
    formatted = format_notes_structure(short, original)
    update_notes(pptx_path="deck.pptx", slide_number=slide_num, 
                 notes_text=formatted["formatted_text"], in_place=True)
```

**After:**
```python
# Read all slides at once
notes = read_notes_batch(pptx_path="deck.pptx", slide_range="1-10")

# Process all...
notes_data = [process(slide) for slide in notes["slides"]]

# Apply all changes atomically with automatic formatting
result = process_notes_workflow(pptx_path="deck.pptx", 
                                notes_data=notes_data, in_place=True)
```

### Performance Comparison

For processing 50 slides:

| Metric | Single-Slide | Batch Operations | Improvement |
|--------|-------------|------------------|-------------|
| Read calls | 50 | 1 | **50x fewer** |
| Update calls | 50 | 1 | **50x fewer** |
| Formatting | Manual 50x | Automatic | **Simpler** |
| Rollback | Not available | Automatic | **Safer** |

## Documentation

- **MCP_AGENT_INSTRUCTIONS.md**: Comprehensive guide for AI agents
- **AGENTS.md**: Overview and workflow examples
- **test_batch_operations.py**: Unit tests with usage examples
- **demo_batch_operations.py**: Interactive demonstration

## Best Practices

1. **Use batch operations for multiple slides**: More efficient than individual calls
2. **Validate inputs first**: Check slide count before batch operations
3. **Handle errors gracefully**: Check `success` field in results
4. **Provide progress feedback**: Keep users informed during processing
5. **Choose the right tool**:
   - Single slide: Use `read_notes` + `update_notes`
   - Multiple slides with LLM: Use `read_notes_batch` + `process_notes_workflow`
   - Custom formatting: Use `read_notes_batch` + `update_notes_batch`

## Future Enhancements

Potential improvements for future versions:

- Parallel processing of independent slides
- Progress callbacks for long-running operations
- Partial success handling with detailed per-slide status
- Batch operations for other slide content (text, images)
- Streaming results for very large presentations

## Support

For issues, questions, or contributions:
- Check the test suite for usage examples
- Run the demo script to see operations in action
- Refer to MCP_AGENT_INSTRUCTIONS.md for detailed documentation
