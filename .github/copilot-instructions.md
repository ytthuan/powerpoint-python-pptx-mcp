# GitHub Copilot Instructions

## Project context

This repository is a **project for building automated processes for PPTX notes and more**. It includes an MCP server for processing, managing, and updating PowerPoint speaker notes.

The project includes:
- Automated PPTX speaker notes processing via MCP server tools
- Utilities for reading, updating, and managing PPTX files
- Support for multi-language note processing (Vietnamese/English - can be changed as needed)

Primary audience: Developers and content creators working with PowerPoint presentations.

## What to generate

- Focus on building and improving automated PPTX processing tools and scripts.
- When working with speaker notes, they should be written in **Vietnamese** (or target language - can be changed as needed), using a **casual, conversational** tone suitable for a live presentation.
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

When the user asks to translate or edit speaker notes inside a `.pptx`:

- Use the MCP server tools for all operations.
- **Default engine:** use `--engine zip` (this edits only `notesSlide*.xml` parts inside the PPTX zip). This is the safest option and preserves slide structure, animations, and transitions.
- Avoid using the `python-pptx` write path unless the user explicitly requests it (it rewrites the whole PPTX package and can cause unintended changes in complex decks).
- Never change slide content or layout; only change speaker notes. If a slide note is empty, keep it empty.
- Use Vietnamese speaker note style per this file: address as "anh/chị", use "chúng ta", keep sentences short and speakable.

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
   - **Automated**: AI agents handle translation and summarization using their own LLM capabilities and orchestrate tool calls.
   - **Manual**: When updating notes manually, use the appropriate MCP tools like `update_notes` or `update_notes_batch`.
   - Review the formatted notes before applying them back to the PPTX.
   - Use safe zip-based editing tools where possible to preserve animations.

### Commands
- Always use `python3` instead of `python` to run the commands.
- Always use `pip3` instead of `pip` to install dependencies.
- Setup (one-time):
	- `python3 -m venv .venv`
	- `source .venv/bin/activate`
	- `pip3 install -r requirements.txt`

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
