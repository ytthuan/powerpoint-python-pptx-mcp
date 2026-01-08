# GitHub Copilot Instructions

## Project context

This repository is a **project for building automated processes for PPTX notes and more**. It includes tools and scripts for processing, translating, and managing PowerPoint speaker notes using Azure Foundry Models Response API.

The project includes:
- Automated PPTX speaker notes processing with translation and summarization
- Integration with Azure Foundry Models Response API for AI-powered note generation
- Utilities for reading, updating, and managing PPTX files
- Support for multi-language note processing (Vietnamese/English)

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

When the user asks to translate or edit speaker notes inside a `.pptx`:

- Prefer using the existing CLI at `scripts/pptx_notes.py` for basic operations.
- Use `scripts/update_notes_format.py` for automated processing with Azure Foundry Models Response API.
- **Default engine:** use `--engine zip` (this edits only `notesSlide*.xml` parts inside the PPTX zip). This is the safest option and preserves slide structure, animations, and transitions.
- Avoid using the `python-pptx` write path unless the user explicitly requests it (it rewrites the whole PPTX package and can cause unintended changes in complex decks).
- Never change slide content or layout; only change speaker notes. If a slide note is empty, keep it empty.
- Use Vietnamese speaker note style per this file: address as "anh/chị", use "chúng ta", keep sentences short and speakable.

### Automated Note Processing with Azure Foundry Models

The project includes `scripts/update_notes_format.py` which uses Azure Foundry Models Response API to automatically:

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
   - **Automated**: Use `scripts/update_notes_format.py` to process notes with Azure Foundry Models
     - Use `--batch-size` to control parallel processing (default: 5)
     - Use `--resume` to continue after interruptions
     - Use `--dry-run` to test without API calls
   - **Manual**: When updating notes manually: first dump current notes, then create a separate JSON file with long/short versions for the target slides
   - Review the formatted notes before applying them back to the PPTX
   - Apply using the zip engine to preserve animations
### Commands
- Always use `python3` instead of `python` to run the commands.
- Always use `pip3` instead of `pip` to install dependencies.
- Setup (one-time):
	- `python3 -m venv .venv`
	- `source .venv/bin/activate`
	- `pip3 install -r requirements.txt`
	- Set environment variables:
	  - `AZURE_AI_PROJECT_ENDPOINT`: Your Azure AI Project endpoint
	  - `MODEL_DEPLOYMENT_NAME`: Your model deployment name

- Dump notes to JSON:
	- `python3 scripts/pptx_notes.py dump "path/to/deck.pptx"`

- Process notes with Azure Foundry Models (automated translation and summarization):
	- `python3 scripts/update_notes_format.py --input "path/to/notes.json" --pptx "path/to/deck.pptx" --output-language vietnamese`
	- Options:
	  - `--endpoint`: Azure AI Project endpoint (or use env var)
	  - `--deployment-name`: Model deployment name (or use env var)
	  - `--output-language`: Target language (vietnamese/english, default: vietnamese)
	  - `--pptx`: PPTX file to update automatically after processing
	  - `--in-place`: Update PPTX in-place (default: creates new file)
	  - `--batch-size`: Number of slides to process in parallel (default: 5)
	  - `--status-file`: Path to status tracking file (default: input_file.status.json)
	  - `--resume`: Resume from status file, skipping already successful slides
	  - `--dry-run`: Test processing without making API calls

- Apply updates manually **in-place** (safe overwrite via temp file):
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
