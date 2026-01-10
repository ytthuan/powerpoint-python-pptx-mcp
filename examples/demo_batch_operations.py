#!/usr/bin/env python3
"""
Demonstration script for batch operations in MCP server.

This script shows how to use the new batch operations to efficiently
process multiple slides in a PowerPoint presentation.
"""

import asyncio
from pathlib import Path

from mcp_server.tools.notes_tools import (
    handle_read_notes_batch,
    handle_update_notes_batch,
    handle_process_notes_workflow,
)


async def demo_read_batch():
    """Demonstrate batch reading of notes."""
    print("\n" + "=" * 60)
    print("Demo 1: Reading Notes from Multiple Slides")
    print("=" * 60)

    test_pptx = Path("test_data/test_presentation.pptx")
    if not test_pptx.exists():
        print("❌ Test PPTX not found. Run the test suite first.")
        return

    # Read notes from slides 1-3
    print("\n📖 Reading notes from slides 1-3...")
    result = await handle_read_notes_batch({"pptx_path": str(test_pptx), "slide_range": "1-3"})

    print(f"✅ Success: {result['success']}")
    print(f"📊 Total slides read: {result['total_slides']}")
    print("\nNotes preview:")
    for slide in result["slides"]:
        notes = slide["notes"]
        if notes:
            preview = notes[:50] + "..." if len(notes) > 50 else notes
            print(f"  • Slide {slide['slide_number']}: {preview}")
        else:
            print(f"  • Slide {slide['slide_number']}: (no notes)")


async def demo_update_batch():
    """Demonstrate batch updating of notes."""
    print("\n" + "=" * 60)
    print("Demo 2: Updating Notes for Multiple Slides")
    print("=" * 60)

    test_pptx = Path("test_data/test_presentation.pptx")
    if not test_pptx.exists():
        print("❌ Test PPTX not found. Run the test suite first.")
        return

    # Create a temporary copy for demonstration
    import shutil
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    shutil.copy2(test_pptx, tmp_path)

    print("\n📝 Updating slides 1 and 2 in temporary file...")

    updates = [
        {
            "slide_number": 1,
            "notes_text": (
                "- Short version:\nDemo short notes for slide 1\n\n"
                "- Original:\nThis is a demonstration of batch update capabilities."
            ),
        },
        {
            "slide_number": 2,
            "notes_text": (
                "- Short version:\nDemo short notes for slide 2\n\n"
                "- Original:\nAnother example of batch updating speaker notes."
            ),
        },
    ]

    result = await handle_update_notes_batch(
        {"pptx_path": str(tmp_path), "updates": updates, "in_place": True}
    )

    print(f"✅ Success: {result['success']}")
    print(f"📊 Updated slides: {result['updated_slides']}")
    print(f"🎯 Slides affected: {result['slides']}")

    # Verify the updates
    print("\n🔍 Verifying updates...")
    verify_result = await handle_read_notes_batch(
        {"pptx_path": str(tmp_path), "slide_numbers": [1, 2]}
    )

    for slide in verify_result["slides"]:
        print(f"\n  Slide {slide['slide_number']}:")
        print(f"  {slide['notes'][:100]}...")

    # Cleanup
    tmp_path.unlink()
    print("\n🧹 Cleaned up temporary file")


async def demo_workflow():
    """Demonstrate complete workflow with formatting."""
    print("\n" + "=" * 60)
    print("Demo 3: Complete Workflow with Automatic Formatting")
    print("=" * 60)

    test_pptx = Path("test_data/test_presentation.pptx")
    if not test_pptx.exists():
        print("❌ Test PPTX not found. Run the test suite first.")
        return

    # Create a temporary copy
    import shutil
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    shutil.copy2(test_pptx, tmp_path)

    print("\n🎯 Processing slides with automatic formatting...")

    # Simulated LLM-processed content
    notes_data = [
        {
            "slide_number": 1,
            "short_text": "Chào mừng anh chị đến với bài thuyết trình",
            "original_text": (
                "Chào mừng anh chị đến với bài thuyết trình của chúng ta hôm nay. "
                "Chúng ta sẽ cùng tìm hiểu về các tính năng mới."
            ),
        },
        {
            "slide_number": 2,
            "short_text": "Tính năng batch operations giúp xử lý nhanh hơn",
            "original_text": (
                "Tính năng batch operations cho phép chúng ta xử lý nhiều slide "
                "cùng lúc, giúp tăng hiệu suất và giảm thời gian xử lý."
            ),
        },
    ]

    result = await handle_process_notes_workflow(
        {"pptx_path": str(tmp_path), "notes_data": notes_data, "in_place": True}
    )

    print(f"✅ Success: {result['success']}")
    print(f"📊 Formatted slides: {result.get('formatted_slides', 0)}")
    print(f"📊 Updated slides: {result['updated_slides']}")
    print(f"🎯 Workflow type: {result.get('workflow', 'N/A')}")

    # Verify the formatting
    print("\n🔍 Verifying formatted notes...")
    verify_result = await handle_read_notes_batch(
        {"pptx_path": str(tmp_path), "slide_numbers": [1, 2]}
    )

    for slide in verify_result["slides"]:
        print(f"\n  Slide {slide['slide_number']}:")
        notes_lines = slide["notes"].split("\n")
        for line in notes_lines[:4]:  # Show first 4 lines
            print(f"  {line}")
        print("  ...")

    # Cleanup
    tmp_path.unlink()
    print("\n🧹 Cleaned up temporary file")


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("BATCH OPERATIONS DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo showcases the new batch operations for efficient")
    print("multi-slide processing in the MCP server.")

    try:
        await demo_read_batch()
        await demo_update_batch()
        await demo_workflow()

        print("\n" + "=" * 60)
        print("✅ All demonstrations completed successfully!")
        print("=" * 60)
        print("\nKey Benefits of Batch Operations:")
        print("  • 🚀 Faster execution (fewer round-trips)")
        print("  • 🔒 Atomic updates (all succeed or all fail)")
        print("  • ✅ Built-in validation and error handling")
        print("  • 📊 Better progress tracking")
        print("  • 🎯 Automatic formatting (process_notes_workflow)")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
