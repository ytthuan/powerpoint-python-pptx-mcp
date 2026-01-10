# Agent Instructions - Quick Reference

> 📖 **Detailed, tool-accurate guidance lives in** `.github/skills/pptx-mcp-server/SKILL.md`

## What this repo is for

Automated PPTX processing via an MCP server, with a primary focus on **speaker notes** workflows (read/translate/summarize/update).

## Non-negotiables (speaker notes work)

- **Only modify speaker notes**, not slide content or layout, unless explicitly requested
- **Do NOT add new slides** unless explicitly requested
- **Keep empty notes empty**
- Keep changes minimal and reversible; prefer batch + atomic updates for multi-slide edits

## Vietnamese speaker notes style (when generating Vietnamese notes - the language can be changed as needed)

- Address audience as **“anh/chị”** (not “bạn”, not “quý vị”)
- Use **“chúng ta”** for shared actions/goals
- Keep sentences short, speakable, conversational

## Required notes structure

Always provide **two versions**:

```
- Short version:
[Brief summary - 30-50% of original length]

- Original:
[Full content with all details and explanations]
```

## Recommended workflow (multi-slide notes)

Use **one batch read + one atomic write**:

```python
# 1) Read notes in batch
notes = await read_notes_batch(pptx_path="deck.pptx", slide_range="1-20")

# 2) Generate content (LLM side) and preserve empty notes
notes_data = []
for slide in notes["slides"]:
    if not slide["notes"]:
        continue
    translated = llm.translate(slide["notes"], target="vietnamese")
    short = llm.summarize(translated, length_percent=40)
    notes_data.append(
        {
            "slide_number": slide["slide_number"],
            "short_text": short,
            "original_text": translated,
        }
    )

# 3) Validate + format + apply atomically (server side)
result = await process_notes_workflow(pptx_path="deck.pptx", notes_data=notes_data, in_place=True)
```

## Tool choice (notes)

- **Multi-slide**: `read_notes_batch` → `process_notes_workflow` (preferred) or `update_notes_batch`
- **Single-slide**: `read_notes` → `update_notes`

## Setup (local dev)

```bash
source .venv/bin/activate  # macOS/Linux
export MCP_WORKSPACE_DIRS=/path/to/presentations
```
