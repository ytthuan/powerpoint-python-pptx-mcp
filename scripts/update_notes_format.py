#!/usr/bin/env python3
"""
Script to update speaker notes to include both short and original versions.
Uses Azure Foundry Models Response API to translate and generate short versions.
Skips empty notes.

⚠️ DEPRECATION WARNING ⚠️
==========================
This script is DEPRECATED and will be removed in a future version.
Please use the MCP server tools with the notes_tools workflow instead.

Migration guide: See MIGRATION.md for instructions on transitioning to MCP tools.

The MCP server provides:
- Better error handling and validation
- Consistent API across all operations  
- Enhanced security features
- Structured logging and monitoring
- Type safety and comprehensive testing

For MCP server usage, see README.md and AGENTS.md documentation.
==========================
"""

import json
import os
import re
import sys
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv

load_dotenv()


# Show deprecation warning
def _show_deprecation_warning():
    """Display deprecation warning to users."""
    warning_msg = """
╔═══════════════════════════════════════════════════════════════════════╗
║                      ⚠️  DEPRECATION WARNING ⚠️                        ║
╠═══════════════════════════════════════════════════════════════════════╣
║  This script (update_notes_format.py) is DEPRECATED and will be      ║
║  removed in a future version.                                         ║
║                                                                        ║
║  Please use the MCP server notes_tools workflow instead:              ║
║  - Better error handling and validation                               ║
║  - Consistent API across all operations                               ║
║  - Enhanced security features                                         ║
║  - Structured logging and monitoring                                  ║
║                                                                        ║
║  See MIGRATION.md for migration instructions.                         ║
║  See README.md for MCP server usage.                                  ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
    print(warning_msg, file=sys.stderr)
    warnings.warn(
        "update_notes_format.py is deprecated. Use MCP server notes_tools workflow instead. "
        "See MIGRATION.md for migration guide.",
        DeprecationWarning,
        stacklevel=2
    )


_show_deprecation_warning()

try:
    from azure.identity import DefaultAzureCredential
    from azure.ai.projects import AIProjectClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Warning: Azure packages not installed. Install with: pip install azure-identity azure-ai-projects")


def is_vietnamese(text):
    """Check if text contains Vietnamese characters."""
    vietnamese_chars = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', re.IGNORECASE)
    return bool(vietnamese_chars.search(text))


def detect_language(text):
    """Detect if text is Vietnamese or English."""
    if not text or not text.strip():
        return "english"  # Default to English for empty text
    
    # Check for Vietnamese characters
    if is_vietnamese(text):
        return "vietnamese"
    else:
        return "english"


def create_foundry_client(endpoint, deployment_name):
    """
    Create Azure Foundry client using DefaultAzureCredential.
    
    Args:
        endpoint: Azure AI Project endpoint URL
        deployment_name: Model deployment name (not used here but kept for consistency)
    
    Returns:
        OpenAI client from AIProjectClient
    """
    if not AZURE_AVAILABLE:
        raise ValueError("Azure packages not installed. Install with: pip install azure-identity azure-ai-projects")
    
    try:
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )
        openai_client = project_client.get_openai_client()
        return openai_client
    except Exception as e:
        raise Exception(f"Failed to create Azure Foundry client: {e}. Make sure AZURE_AI_PROJECT_ENDPOINT is set and credentials are configured.")


def create_long_version(original_text, output_language="vietnamese", client=None, deployment_name=None, max_retries=3):
    """
    Create long version by translating if needed.
    
    Args:
        original_text: Original speaker notes text
        output_language: Target language ("vietnamese" or "english", default: "vietnamese")
        client: Azure Foundry OpenAI client
        deployment_name: Model deployment name
        max_retries: Maximum number of retry attempts
    
    Returns:
        Translated text if needed, or original text if already in target language
    """
    if not original_text or not original_text.strip():
        return original_text
    
    # Detect input language
    input_language = detect_language(original_text)
    
    # If output is Vietnamese and text is already Vietnamese, skip translation
    if output_language == "vietnamese" and input_language == "vietnamese":
        return original_text
    
    # If output is English and text is already English, skip translation
    if output_language == "english" and input_language == "english":
        return original_text
    
    # Need to translate
    if client is None or deployment_name is None:
        raise ValueError("Client and deployment_name are required for translation")
    
    # Prepare translation prompt
    if output_language == "vietnamese":
        prompt = f"""Translate the following speaker notes to Vietnamese. Maintain the conversational, speakable tone suitable for a live presentation. Address the audience as 'chúng ta' and use 'chúng ta' when referring to shared actions. Keep sentences short and speakable. Use simple bullet points; avoid long paragraphs unless explicitly requested.

Original speaker notes:
{original_text}

Translated Vietnamese version:"""
    else:
        prompt = f"""Translate the following speaker notes to English. Maintain the conversational, speakable tone suitable for a live presentation. Keep sentences short and speakable.

Original speaker notes:
{original_text}

Translated English version:"""
    
    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model=deployment_name,
                input=prompt
            )
            
            # Extract text from response
            # Response API returns output_text field
            if hasattr(response, 'output_text'):
                translated_text = response.output_text.strip()
            elif hasattr(response, 'output'):
                translated_text = response.output.strip()
            else:
                # Try to get from model_dump if available
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
                translated_text = response_dict.get('output_text', response_dict.get('output', original_text)).strip()
            
            return translated_text
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Warning: Translation failed after {max_retries} attempts: {e}")
                print(f"  Falling back to original text")
                return original_text
    
    return original_text  # Fallback to original if all retries fail


def create_short_version(original_text, output_language="vietnamese", client=None, deployment_name=None, max_retries=3):
    """
    Create a condensed version using Response API (30-50% of original length).
    
    Args:
        original_text: Original speaker notes text (any language)
        output_language: Target language for output ("vietnamese" or "english", default: "vietnamese")
        client: Azure Foundry OpenAI client
        deployment_name: Model deployment name
        max_retries: Maximum number of retry attempts
    
    Returns:
        Brief summary in target language
    """
    if not original_text or not original_text.strip():
        return original_text
    
    if client is None or deployment_name is None:
        raise ValueError("Client and deployment_name are required for summarization")
    
    # Prepare summarization prompt
    language_instruction = ""
    if output_language == "vietnamese":
        language_instruction = "Output language: Vietnamese. Address the audience as 'chúng ta' and use 'chúng ta' when referring to shared actions."
    else:
        language_instruction = "Output language: English."
    
    prompt = f"""Create a concise summary of the following speaker notes.

Requirements:
- Create a brief summary that is 30-50% of the original length
- Preserve the key points and main ideas
- Maintain the conversational, speakable tone
- Use complete sentences
- Focus on the most important information for the presenter
- Output in bullet points for easier reading
- {language_instruction}

Original speaker notes:
{original_text}

Create a concise short version:"""
    
    for attempt in range(max_retries):
        try:
            response = client.responses.create(
                model=deployment_name,
                input=prompt
            )
            
            # Extract text from response
            if hasattr(response, 'output_text'):
                short_version = response.output_text.strip()
            elif hasattr(response, 'output'):
                short_version = response.output.strip()
            else:
                # Try to get from model_dump if available
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
                short_version = response_dict.get('output_text', response_dict.get('output', original_text)).strip()
            
            return short_version
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Warning: Summarization failed after {max_retries} attempts: {e}")
                print(f"  Falling back to first paragraph")
                # Simple fallback: take first paragraph
                paragraphs = [p.strip() for p in original_text.split('\n') if p.strip()]
                if paragraphs:
                    short_version = paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
                else:
                    short_version = original_text[:200] + "..." if len(original_text) > 200 else original_text
                return short_version
    
    # Final fallback
    paragraphs = [p.strip() for p in original_text.split('\n') if p.strip()]
    if paragraphs:
        return paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
    else:
        return original_text[:200] + "..." if len(original_text) > 200 else original_text


def format_notes(original_text, client=None, deployment_name=None, output_language="vietnamese"):
    """
    Format notes with short and original versions using Azure Foundry Response API.
    
    Args:
        original_text: Original speaker notes text
        client: Azure Foundry OpenAI client
        deployment_name: Model deployment name
        output_language: Target language for output ("vietnamese" or "english", default: "vietnamese")
    
    Returns:
        Formatted notes with short and original versions
    """
    if not original_text or not original_text.strip():
        return ""
    
    # Clean up the text
    text = original_text.strip()
    
    # Extract original text if already formatted
    if "- Original:" in text or "- original:" in text:
        if "- Original:" in text:
            parts = text.split("- Original:\n", 1)
            if len(parts) == 2:
                text = parts[1].strip()
        elif "- original:" in text:
            parts = text.split("- original:\n", 1)
            if len(parts) == 2:
                text = parts[1].strip()
    
    # Create long version (translate if needed)
    long_version = text
    if client and deployment_name:
        try:
            long_version = create_long_version(text, output_language=output_language, client=client, deployment_name=deployment_name)
        except Exception as e:
            print(f"  Warning: Long version creation failed: {e}")
            long_version = text  # Fallback to original
    
    # Create short version
    short_version = None
    if client and deployment_name:
        try:
            short_version = create_short_version(long_version, output_language=output_language, client=client, deployment_name=deployment_name)
        except Exception as e:
            print(f"  Warning: Short version creation failed: {e}")
            # Fallback: take first paragraph
            paragraphs = [p.strip() for p in long_version.split('\n') if p.strip()]
            if paragraphs:
                short_version = paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
            else:
                short_version = long_version[:200] + "..." if len(long_version) > 200 else long_version
    else:
        # No client available - use simple fallback
        paragraphs = [p.strip() for p in long_version.split('\n') if p.strip()]
        if paragraphs:
            short_version = paragraphs[0][:200] + "..." if len(paragraphs[0]) > 200 else paragraphs[0]
        else:
            short_version = long_version[:200] + "..." if len(long_version) > 200 else long_version
    
    # Format according to template
    formatted = f"- Short version:\n{short_version}\n\n- Original:\n{long_version}"
    
    return formatted


def load_status_file(status_file_path):
    """
    Load status tracking file.
    
    Args:
        status_file_path: Path to status JSON file
    
    Returns:
        Dictionary with slide statuses, or empty dict if file doesn't exist
    """
    if status_file_path.exists():
        try:
            with open(status_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load status file: {e}")
            return {}
    return {}


def save_status_file(status_file_path, status_data):
    """
    Save status tracking file.
    
    Args:
        status_file_path: Path to status JSON file
        status_data: Dictionary with slide statuses
    """
    try:
        with open(status_file_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: Could not save status file: {e}")


def update_slide_status(status_file_path, status_data, slide_index, status, error=None, lock=None):
    """
    Update status for a specific slide and save to file.
    
    Args:
        status_file_path: Path to status JSON file
        status_data: Dictionary with slide statuses
        slide_index: Slide index (1-based)
        status: Status string ("success", "failed", "processing")
        error: Optional error message
        lock: Optional threading lock for thread-safe updates
    """
    if lock:
        with lock:
            _update_slide_status_internal(status_file_path, status_data, slide_index, status, error)
    else:
        _update_slide_status_internal(status_file_path, status_data, slide_index, status, error)


def _update_slide_status_internal(status_file_path, status_data, slide_index, status, error):
    """Internal function to update slide status (called with lock held if needed)."""
    if 'slides' not in status_data:
        status_data['slides'] = {}
    
    status_data['slides'][str(slide_index)] = {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'error': error if error else None
    }
    
    # Update summary counts
    if 'summary' not in status_data:
        status_data['summary'] = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'processing': 0,
            'skipped': 0
        }
    
    # Recalculate summary
    slides = status_data.get('slides', {})
    status_data['summary'] = {
        'total': len(slides),
        'success': sum(1 for s in slides.values() if s.get('status') == 'success'),
        'failed': sum(1 for s in slides.values() if s.get('status') == 'failed'),
        'processing': sum(1 for s in slides.values() if s.get('status') == 'processing'),
        'skipped': sum(1 for s in slides.values() if s.get('status') == 'skipped')
    }
    
    save_status_file(status_file_path, status_data)


def process_single_slide(slide_data, slide_index, client, deployment, output_language, status_file_path, status_data, lock, dry_run=False):
    """
    Process a single slide's notes.
    
    Args:
        slide_data: Dictionary with slide data (must have 'notes' key)
        slide_index: Slide index (1-based)
        client: Azure Foundry OpenAI client
        deployment: Model deployment name
        output_language: Target language
        status_file_path: Path to status file
        status_data: Status data dictionary
        lock: Threading lock for status updates
        dry_run: If True, skip API calls and simulate processing
    
    Returns:
        Tuple of (slide_index, success: bool, formatted_notes: str, error: str or None)
    """
    notes = slide_data.get('notes', '')
    
    # Skip empty notes
    if not notes or not notes.strip():
        update_slide_status(status_file_path, status_data, slide_index, 'skipped', None, lock)
        return (slide_index, True, notes, None)
    
    # Mark as processing
    update_slide_status(status_file_path, status_data, slide_index, 'processing', None, lock)
    
    # Dry run: simulate processing without API calls
    if dry_run:
        time.sleep(0.1)  # Simulate processing time
        # Create a simple formatted version without API calls
        formatted_notes = f"- Short version:\n[DRY RUN: Short version of slide {slide_index}]\n\n- Original:\n{notes}"
        update_slide_status(status_file_path, status_data, slide_index, 'success', None, lock)
        return (slide_index, True, formatted_notes, None)
    
    try:
        formatted_notes = format_notes(notes, client=client, deployment_name=deployment, output_language=output_language)
        update_slide_status(status_file_path, status_data, slide_index, 'success', None, lock)
        return (slide_index, True, formatted_notes, None)
    except Exception as e:
        error_msg = str(e)
        update_slide_status(status_file_path, status_data, slide_index, 'failed', error_msg, lock)
        return (slide_index, False, notes, error_msg)


def process_json_file(input_path, output_path, pptx_path=None, endpoint=None, deployment_name=None, output_language="vietnamese", in_place=False, status_file_path=None, batch_size=5, resume=False, dry_run=False):
    """
    Process the JSON file and update all notes using Azure Foundry Response API with parallel processing.
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        pptx_path: Optional path to PPTX file to update
        endpoint: Azure AI Project endpoint (or use AZURE_AI_PROJECT_ENDPOINT env var)
        deployment_name: Model deployment name (or use MODEL_DEPLOYMENT_NAME env var)
        output_language: Target language ("vietnamese" or "english", default: "vietnamese")
        in_place: Whether to update PPTX in-place (default: False)
        status_file_path: Path to status tracking file (default: input_path + ".status.json")
        batch_size: Number of slides to process in parallel (default: 5)
        resume: Whether to resume from status file, skipping already successful slides (default: False)
        dry_run: If True, skip API calls and simulate processing (default: False)
    """
    # Initialize status file path
    if status_file_path is None:
        status_file_path = Path(str(input_path) + ".status.json")
    else:
        status_file_path = Path(status_file_path)
    
    # Load existing status if resuming
    status_data = load_status_file(status_file_path) if resume else {}
    if resume and status_data:
        print(f"Resuming from status file: {status_file_path}")
        summary = status_data.get('summary', {})
        print(f"  Already processed: {summary.get('success', 0)} success, {summary.get('failed', 0)} failed")
    
    # Initialize Azure Foundry client
    client = None
    deployment = None
    
    if AZURE_AVAILABLE:
        endpoint = endpoint or os.getenv("AZURE_AI_PROJECT_ENDPOINT")
        deployment = deployment_name or os.getenv("MODEL_DEPLOYMENT_NAME")
        
        if endpoint and deployment:
            try:
                client = create_foundry_client(endpoint, deployment)
                print(f"Connected to Azure Foundry: {endpoint}")
                print(f"Using deployment: {deployment}")
            except Exception as e:
                print(f"Warning: Failed to create Azure Foundry client: {e}")
                print("Continuing without LLM - will use fallback...")
        else:
            missing = []
            if not endpoint:
                missing.append("AZURE_AI_PROJECT_ENDPOINT")
            if not deployment:
                missing.append("MODEL_DEPLOYMENT_NAME")
            print(f"Warning: Missing environment variables: {', '.join(missing)}")
            print("Continuing without LLM - will use fallback...")
    else:
        print("Warning: Azure packages not installed. Install with: pip install azure-identity azure-ai-projects")
        print("Continuing without LLM - will use fallback...")
    
    # Load input data
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # If resuming and output file exists, load it to preserve already processed slides
    if resume and Path(output_path).exists():
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            # Merge existing processed notes into data
            for idx, existing_slide in enumerate(existing_data.get('slides', [])):
                if idx < len(data['slides']):
                    slide_status = status_data.get('slides', {}).get(str(idx + 1), {})
                    if slide_status.get('status') == 'success':
                        # Preserve the already processed notes
                        data['slides'][idx]['notes'] = existing_slide.get('notes', data['slides'][idx].get('notes', ''))
        except Exception as e:
            print(f"Warning: Could not load existing output file for resume: {e}")
            print("Starting fresh...")
    
    # Prepare slides for processing
    slides_to_process = []
    for idx, slide in enumerate(data['slides'], start=1):
        notes = slide.get('notes', '')
        
        # Skip empty notes
        if not notes or not notes.strip():
            update_slide_status(status_file_path, status_data, idx, 'skipped', None, None)
            continue
        
        # If resuming, skip already successful slides
        if resume:
            slide_status = status_data.get('slides', {}).get(str(idx), {})
            if slide_status.get('status') == 'success':
                continue
        
        slides_to_process.append((idx, slide))
    
    total_slides = len(slides_to_process)
    print(f"\nProcessing {total_slides} slides with notes...")
    print(f"Output language: {output_language}")
    print(f"Batch size: {batch_size} (parallel processing)")
    print(f"Status file: {status_file_path}")
    if dry_run:
        print(f"⚠️  DRY RUN MODE: No API calls will be made")
    
    # Thread-safe lock for status updates
    status_lock = Lock()
    
    # Process slides in parallel batches
    updated_count = 0
    failed_count = 0
    skipped_count = 0
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all tasks
        future_to_slide = {}
        for slide_index, slide_data in slides_to_process:
            future = executor.submit(
                process_single_slide,
                slide_data,
                slide_index,
                client,
                deployment,
                output_language,
                status_file_path,
                status_data,
                status_lock,
                dry_run
            )
            future_to_slide[future] = (slide_index, slide_data)
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_slide):
            slide_index, slide_data = future_to_slide[future]
            completed += 1
            
            try:
                idx, success, formatted_notes, error = future.result()
                
                # Update slide data
                data['slides'][idx - 1]['notes'] = formatted_notes
                
                if success:
                    if error is None:
                        print(f"  [{completed}/{total_slides}] Slide {idx}: ✓")
                        updated_count += 1
                    else:
                        print(f"  [{completed}/{total_slides}] Slide {idx}: ⊘ (skipped)")
                        skipped_count += 1
                else:
                    print(f"  [{completed}/{total_slides}] Slide {idx}: ✗ Error: {error}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  [{completed}/{total_slides}] Slide {slide_index}: ✗ Exception: {e}")
                update_slide_status(status_file_path, status_data, slide_index, 'failed', str(e), status_lock)
                failed_count += 1
    
    # Write updated JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Final status summary
    final_status = load_status_file(status_file_path)
    summary = final_status.get('summary', {})
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"  - Total slides: {len(data['slides'])}")
    print(f"  - Success: {summary.get('success', updated_count)}")
    print(f"  - Failed: {summary.get('failed', failed_count)}")
    print(f"  - Skipped (empty): {summary.get('skipped', skipped_count)}")
    print(f"  - Status file: {status_file_path}")
    print(f"Output written to: {output_path}")
    print(f"{'='*60}")
    
    # Update PPTX file if path provided
    if pptx_path:
        pptx_path = Path(pptx_path)
        if not pptx_path.exists():
            print(f"\nWarning: PPTX file not found: {pptx_path}")
            print("Skipping PPTX update.")
        else:
            print(f"\nUpdating PPTX file: {pptx_path}")
            try:
                # Import the apply function from pptx_notes
                script_dir = Path(__file__).parent
                sys.path.insert(0, str(script_dir))
                from pptx_notes import apply_notes_zip_in_place, apply_notes_zip
                
                if in_place:
                    apply_notes_zip_in_place(pptx_path, Path(output_path))
                else:
                    # Create output PPTX path
                    pptx_out = pptx_path.with_name(pptx_path.stem + ".updated.pptx")
                    apply_notes_zip(pptx_path, Path(output_path), pptx_out)
                    print(f"Updated PPTX written to: {pptx_out}")
            except Exception as e:
                print(f"Error updating PPTX file: {e}")
                print("You can manually update the PPTX using:")
                print(f"  python scripts/pptx_notes.py apply \"{pptx_path}\" \"{output_path}\" --engine zip")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update speaker notes with short and original versions using Azure Foundry Models Response API"
    )
    parser.add_argument(
        '--endpoint',
        type=str,
        help='Azure AI Project endpoint (or set AZURE_AI_PROJECT_ENDPOINT environment variable)'
    )
    parser.add_argument(
        '--deployment-name',
        type=str,
        help='Model deployment name (or set MODEL_DEPLOYMENT_NAME environment variable)'
    )
    parser.add_argument(
        '--output-language',
        type=str,
        choices=['vietnamese', 'english'],
        default='vietnamese',
        help='Target language for output (default: vietnamese)'
    )
    parser.add_argument(
        '--input',
        type=Path,
        help='Input JSON file (default: src/deck/current-notes-dump.json)'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output JSON file (default: same as input)'
    )
    parser.add_argument(
        '--pptx',
        type=Path,
        help='PPTX file to update with processed notes (optional)'
    )
    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Update PPTX file in-place (default: create new file with .updated.pptx suffix)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5,
        help='Number of slides to process in parallel (default: 5)'
    )
    parser.add_argument(
        '--status-file',
        type=Path,
        help='Path to status tracking file (default: input_file + .status.json)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from status file, skipping already successful slides'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode: test processing without making API calls'
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    input_file = args.input or (repo_root / 'src' / 'deck' / 'current-notes-dump.json')
    output_file = args.output or input_file
    
    process_json_file(
        input_file, 
        output_file, 
        pptx_path=args.pptx,
        endpoint=args.endpoint,
        deployment_name=args.deployment_name,
        output_language=args.output_language,
        in_place=args.in_place,
        status_file_path=args.status_file,
        batch_size=args.batch_size,
        resume=args.resume,
        dry_run=args.dry_run
    )

