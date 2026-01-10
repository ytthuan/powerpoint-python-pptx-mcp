# Slide Visibility Feature Documentation

## Overview

This feature adds comprehensive support for reading and managing slide visibility (hidden/visible) attributes in PowerPoint presentations. This enables users to programmatically control which slides are shown during a presentation, making it easy to create presentations with optional or backup content.

## Features Added

### Core PPTXHandler Methods

#### `is_slide_hidden(slide_number: int) -> bool`
Check if a specific slide is hidden.

```python
from mcp_server.core.pptx_handler import PPTXHandler

handler = PPTXHandler("presentation.pptx")
is_hidden = handler.is_slide_hidden(2)  # Check if slide 2 is hidden
print(f"Slide 2 is {'hidden' if is_hidden else 'visible'}")
```

#### `set_slide_hidden(slide_number: int, hidden: bool)`
Set slide visibility (hide or show a slide).

```python
handler.set_slide_hidden(2, True)   # Hide slide 2
handler.set_slide_hidden(3, False)  # Show slide 3
handler.save("updated.pptx")        # Save changes
```

#### `get_slides_metadata(include_hidden: bool = True) -> List[Dict]`
Get metadata for all slides including their visibility status.

```python
# Get all slides (including hidden)
all_slides = handler.get_slides_metadata(include_hidden=True)

# Get only visible slides
visible_slides = handler.get_slides_metadata(include_hidden=False)

for slide in all_slides:
    print(f"Slide {slide['slide_number']}: {slide['title']} - {'HIDDEN' if slide['hidden'] else 'VISIBLE'}")
```

### MCP Tools

#### `read_slides_metadata`
Get metadata for all slides with their visibility status.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `include_hidden` (optional, default: true): Include hidden slides in results

**Response:**
```json
{
  "pptx_path": "presentation.pptx",
  "total_slides": 10,
  "slides": [
    {
      "slide_number": 1,
      "title": "Introduction",
      "hidden": false,
      "slide_id": 256
    },
    {
      "slide_number": 2,
      "title": "Backup Slide",
      "hidden": true,
      "slide_id": 257
    }
  ]
}
```

#### `set_slide_visibility`
Hide or show a specific slide.

**Parameters:**
- `pptx_path` (required): Path to the PPTX file
- `slide_number` (required): Slide number (1-indexed)
- `hidden` (required): True to hide, False to show
- `output_path` (optional): Output path for the modified file

**Response:**
```json
{
  "success": true,
  "output_path": "presentation.edited.pptx",
  "slide_number": 2,
  "hidden": true
}
```

#### Enhanced: `read_slide_content`
Now includes `hidden` status in the response and supports filtering.

**New Parameters:**
- `include_hidden` (optional, default: true): When reading all slides, filter by visibility

**Updated Response:**
```json
{
  "slide_number": 1,
  "title": "Introduction",
  "text": "Welcome to the presentation",
  "shapes": [...],
  "hidden": false
}
```

#### Enhanced: `read_presentation_info`
Now includes visibility statistics.

**Updated Response:**
```json
{
  "file_path": "presentation.pptx",
  "file_name": "presentation.pptx",
  "slide_count": 10,
  "visible_slides": 8,
  "hidden_slides": 2,
  "slide_size": {
    "width": 9144000,
    "height": 6858000
  }
}
```

## Use Cases

### 1. Filter Visible Slides Only
Read only the slides that will be shown in the presentation:

```python
handler = PPTXHandler("presentation.pptx")
visible_slides = handler.get_slides_metadata(include_hidden=False)
for slide in visible_slides:
    print(f"Slide {slide['slide_number']}: {slide['title']}")
```

### 2. Create Backup Slides
Hide slides that contain backup information:

```python
handler = PPTXHandler("presentation.pptx")
# Hide backup slides
for slide_num in [10, 11, 12]:  # Backup slides
    handler.set_slide_hidden(slide_num, True)
handler.save("presentation_ready.pptx")
```

### 3. Conditional Content
Show/hide slides based on audience:

```python
handler = PPTXHandler("presentation.pptx")
# Show technical details for technical audience
if audience == "technical":
    handler.set_slide_hidden(5, False)  # Technical deep dive
    handler.set_slide_hidden(6, False)  # Advanced features
else:
    handler.set_slide_hidden(5, True)
    handler.set_slide_hidden(6, True)
handler.save(f"presentation_{audience}.pptx")
```

### 4. Presentation Statistics
Get visibility statistics:

```python
handler = PPTXHandler("presentation.pptx")
info = handler.get_presentation_info()
print(f"Total slides: {info['slide_count']}")
print(f"Visible: {info['visible_slides']}")
print(f"Hidden: {info['hidden_slides']}")
```

## Technical Details

### OOXML Implementation
The feature uses the standard OOXML `show` attribute on `<p:sldId>` elements:
- `show="0"`: Slide is hidden
- `show="1"` or no attribute: Slide is visible (default)

This ensures compatibility with all PowerPoint versions and other OOXML-compliant applications.

### Example XML
```xml
<p:sldIdLst>
  <p:sldId id="256" r:id="rId2"/>           <!-- Visible slide -->
  <p:sldId id="257" r:id="rId3" show="0"/>  <!-- Hidden slide -->
  <p:sldId id="258" r:id="rId4"/>           <!-- Visible slide -->
</p:sldIdLst>
```

## Testing

Run the included tests to verify functionality:

```bash
# Feature tests
python3 -m pytest tests/integration/test_slide_visibility.py

# Integration tests
python3 -m pytest tests/integration/test_slide_visibility_integration.py

# Demo script
python3 examples/demo_slide_visibility.py

# MCP server tests
python3 tests/integration/test_mcp_server.py --quick
```

All tests should pass with no errors.

## Security

- Uses secure temporary file creation (`tempfile.mkstemp`)
- No security vulnerabilities found in CodeQL scan
- All file operations are validated and error-handled

## Compatibility

- Works with all PowerPoint file formats (.pptx)
- Compatible with PowerPoint 2007 and later
- Uses standard OOXML specification
- Cross-platform (Windows, macOS, Linux)

## Future Enhancements

Possible future improvements:
- Batch hide/show operations for multiple slides
- Hide/show by criteria (e.g., all slides with specific tag)
- Undo/redo functionality
- Visibility presets or profiles
