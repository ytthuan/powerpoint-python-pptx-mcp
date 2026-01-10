---
name: pptx-mcp-server
description: Use this skill when working with PPTX files via the repository’s MCP server—reading slide content, managing speaker notes (including Vietnamese short/original format), doing safe batch notes updates, replacing text, and toggling slide visibility.
---
## Skill Instructions

This skill guides you to use the repository’s **PPTX MCP Server** tools correctly and efficiently.

### When to use this skill

Use this skill when the user asks to:
- Read PPTX slide content (text/images/metadata/visibility)
- Read/update speaker notes (especially translation + short/original formatting)
- Perform multi-slide notes workflows (batch read + batch update, atomic)
- Replace text in slide content or speaker notes (literal or regex)
- Hide/show slides, or other slide management tasks
- Diagnose MCP server health

### Guardrails (apply to all tasks)

- **Do not change slide content/layout** unless explicitly requested.
- **Do not add new slides** unless explicitly requested.
- **Keep empty notes empty** (do not invent notes for slides with empty notes unless asked).
- Prefer **batch tools** for multi-slide work to minimize round trips and keep updates atomic.
- Prefer **safe zip-based notes editing** tools for speaker notes updates to preserve animations/transitions.

### Vietnamese speaker notes style (when generating Vietnamese notes)

- Address the audience as **“anh/chị”** (not “bạn”, not “quý vị”).
- Use **“chúng ta”** for shared actions/goals.
- Keep sentences **short, speakable**, and conversational.
- Required structure (two versions):

```
- Short version:
[Brief summary - 30-50% of original length]

- Original:
[Full content with all details and explanations]
```

### Best-practice workflows

#### Batch translate/summarize speaker notes (recommended)

1) **Read notes in batch** with `read_notes_batch` (use `slide_range` for consecutive slides).
2) **Generate content** with the LLM (translation + short summary), preserving empties.
3) **Apply atomically** with `process_notes_workflow` (formats into short/original and updates in one atomic operation).

#### Targeted notes update (single slide)

- Read context with `read_notes` (or `read_notes_batch`), then update with `update_notes`.
- If updating many slides, use `update_notes_batch`.

#### Replace text

- Use `replace_text` for either:
  - `target="slide_notes"` (speaker notes), or
  - `target="slide_content"` (slide shape text)
- Use `dry_run=true` to preview changes before writing.

### Tool catalog (authoritative names)

#### Read tools

- **`read_slide_content`**: comprehensive slide content (text/shapes/images + visibility status)
- **`read_slide_text`**: all text from a slide
- **`read_slide_images`**: image info from a slide
- **`read_presentation_info`**: presentation metadata (slide count, dimensions, visibility stats)
- **`read_slides_metadata`**: metadata for all slides including visibility

#### Edit tools (slide content)

- **`update_slide_text`**: update a specific shape’s text by `shape_id`
- **`replace_slide_image`**: replace an image shape by `shape_id`
- **`add_text_box`**: add a new text box to a slide
- **`add_image`**: add a new image to a slide
- **`replace_slide_content`**: replace most/all slide text content with structured content
- **`update_slide_content`**: update title/specific shapes/add text boxes without replacing everything

#### Slide management tools

- **`add_slide`**: add a slide (only when explicitly requested)
- **`delete_slide`**: delete a slide (only when explicitly requested)
- **`duplicate_slide`**: duplicate a slide (only when explicitly requested)
- **`change_slide_layout`**: change a slide’s layout
- **`set_slide_visibility`**: hide/show a slide

#### Speaker notes tools

- **`read_notes`**: read notes from one slide or all slides
- **`read_notes_batch`**: read notes from multiple slides efficiently (`slide_numbers` or `slide_range`)
- **`update_notes`**: update notes for one slide (safe zip-based editing for notes)
- **`update_notes_batch`**: atomic notes update for multiple slides (safe zip-based editing)
- **`format_notes_structure`**: format given `short_text` + `original_text` into the required structure (no content generation)
- **`process_notes_workflow`**: validate + format + apply pre-generated notes for multiple slides atomically

#### Text replacement tool

- **`replace_text`**: replace text in speaker notes or slide content, supports regex + dry-run + in-place/out-of-place

#### Health tool

- **`health_check`**: server health diagnostics (config/cache/metrics)

### Operational notes

- If you need to identify `shape_id` for edits, first call `read_slide_content`.
- For multi-slide operations, prefer `read_notes_batch` + `process_notes_workflow` or `update_notes_batch`.
- Use `in_place=true` only when safe/appropriate; otherwise write to a new file via `output_path`.
