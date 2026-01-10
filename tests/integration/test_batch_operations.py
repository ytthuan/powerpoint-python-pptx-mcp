#!/usr/bin/env python3
"""Unit tests for batch operations in MCP server notes tools."""

import shutil
import tempfile
from pathlib import Path

import pytest

from mcp_server.tools.notes_tools import (
    handle_read_notes_batch,
    handle_update_notes_batch,
    handle_process_notes_workflow,
)
from mcp_server.utils.validators import (
    parse_slide_range,
    validate_slide_numbers,
    validate_batch_updates,
)


from mcp_server.exceptions import (
    InvalidSlideNumberError,
    ValidationError,
)


class TestSlideRangeParsing:
    """Test slide range parsing functionality."""

    def test_parse_slide_range_basic(self):
        """Test basic slide range parsing."""
        result = parse_slide_range("1-5")
        assert result == [1, 2, 3, 4, 5]

    def test_parse_slide_range_single(self):
        """Test single slide range."""
        result = parse_slide_range("3-3")
        assert result == [3]

    def test_parse_slide_range_with_spaces(self):
        """Test range parsing with spaces."""
        result = parse_slide_range("  2  -  4  ")
        assert result == [2, 3, 4]

    def test_parse_slide_range_invalid_format(self):
        """Test invalid range format."""
        with pytest.raises(ValueError, match="Invalid slide range format"):
            parse_slide_range("1-2-3")

    def test_parse_slide_range_non_numeric(self):
        """Test non-numeric range."""
        with pytest.raises(ValueError, match="Invalid slide range numbers"):
            parse_slide_range("a-b")

    def test_parse_slide_range_negative_start(self):
        """Test negative start value."""
        with pytest.raises(ValueError, match="Slide range start must be >= 1"):
            parse_slide_range("0-5")

    def test_parse_slide_range_end_before_start(self):
        """Test end value before start."""
        with pytest.raises(ValueError, match="Slide range end .* must be >= start"):
            parse_slide_range("5-3")


class TestSlideNumbersValidation:
    """Test slide numbers validation."""

    def test_validate_slide_numbers_basic(self):
        """Test basic slide numbers validation."""
        result = validate_slide_numbers([1, 3, 5], max_slides=10)
        assert result == [1, 3, 5]

    def test_validate_slide_numbers_empty_list(self):
        """Test empty list validation."""
        with pytest.raises(ValueError, match="Slide numbers list cannot be empty"):
            validate_slide_numbers([], max_slides=10)

    def test_validate_slide_numbers_not_list(self):
        """Test non-list input."""
        with pytest.raises(ValueError, match="Slide numbers must be a list"):
            validate_slide_numbers("1,2,3", max_slides=10)

    def test_validate_slide_numbers_non_integer(self):
        """Test non-integer slide number."""
        with pytest.raises(ValueError, match="All slide numbers must be integers"):
            validate_slide_numbers([1, "2", 3], max_slides=10)

    def test_validate_slide_numbers_out_of_range(self):
        """Test slide number out of range."""
        with pytest.raises(
            InvalidSlideNumberError, match="Invalid slide number: 15. Must be between 1 and 10"
        ):
            validate_slide_numbers([1, 2, 15], max_slides=10)

    def test_validate_slide_numbers_negative(self):
        """Test negative slide number."""
        with pytest.raises(
            InvalidSlideNumberError, match="Invalid slide number: -1. Must be between 1 and 10"
        ):
            validate_slide_numbers([1, -1, 3], max_slides=10)


class TestBatchUpdatesValidation:
    """Test batch updates validation."""

    def test_validate_batch_updates_basic(self):
        """Test basic batch updates validation."""
        updates = [
            {"slide_number": 1, "notes_text": "Notes 1"},
            {"slide_number": 2, "notes_text": "Notes 2"},
        ]
        result = validate_batch_updates(updates, max_slides=10)
        assert len(result) == 2
        assert result[0]["slide_number"] == 1
        assert result[1]["notes_text"] == "Notes 2"

    def test_validate_batch_updates_empty_list(self):
        """Test empty updates list."""
        with pytest.raises(ValueError, match="Updates list cannot be empty"):
            validate_batch_updates([], max_slides=10)

    def test_validate_batch_updates_not_list(self):
        """Test non-list updates."""
        with pytest.raises(ValueError, match="Updates must be a list"):
            validate_batch_updates({"slide": 1}, max_slides=10)

    def test_validate_batch_updates_missing_slide_number(self):
        """Test update missing slide_number."""
        updates = [{"notes_text": "Notes"}]
        with pytest.raises(ValueError, match="missing required field 'slide_number'"):
            validate_batch_updates(updates, max_slides=10)

    def test_validate_batch_updates_missing_notes_text(self):
        """Test update missing notes_text."""
        updates = [{"slide_number": 1}]
        with pytest.raises(ValueError, match="missing required field 'notes_text'"):
            validate_batch_updates(updates, max_slides=10)

    def test_validate_batch_updates_invalid_slide_number_type(self):
        """Test invalid slide_number type."""
        updates = [{"slide_number": "1", "notes_text": "Notes"}]
        with pytest.raises(ValueError, match="slide_number must be integer"):
            validate_batch_updates(updates, max_slides=10)

    def test_validate_batch_updates_invalid_notes_text_type(self):
        """Test invalid notes_text type."""
        updates = [{"slide_number": 1, "notes_text": 123}]
        with pytest.raises(ValueError, match="notes_text must be string"):
            validate_batch_updates(updates, max_slides=10)


class TestBatchOperations:
    """Test batch operations with actual PPTX file."""

    @pytest.fixture
    def test_pptx_path(self):
        """Get path to test PPTX file."""
        test_path = Path(__file__).parent / "test_data" / "test_presentation.pptx"
        if not test_path.exists():
            pytest.skip("Test PPTX file not found")
        return str(test_path)

    @pytest.fixture
    def temp_pptx_path(self, test_pptx_path):
        """Create temporary copy of test PPTX for modification."""
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        shutil.copy2(test_pptx_path, tmp_path)
        yield str(tmp_path)

        # Cleanup
        if tmp_path.exists():
            tmp_path.unlink()

    @pytest.mark.asyncio
    async def test_read_notes_batch_with_numbers(self, test_pptx_path):
        """Test reading notes from specific slide numbers."""
        result = await handle_read_notes_batch(
            {
                "pptx_path": test_pptx_path,
                "slide_numbers": [1, 3, 5],
            }
        )

        assert result["success"] is True
        assert result["total_slides"] == 3
        assert len(result["slides"]) == 3
        assert result["slides"][0]["slide_number"] == 1
        assert result["slides"][1]["slide_number"] == 3
        assert result["slides"][2]["slide_number"] == 5

    @pytest.mark.asyncio
    async def test_read_notes_batch_with_range(self, test_pptx_path):
        """Test reading notes with slide range."""
        result = await handle_read_notes_batch(
            {
                "pptx_path": test_pptx_path,
                "slide_range": "2-4",
            }
        )

        assert result["success"] is True
        assert result["total_slides"] == 3
        assert len(result["slides"]) == 3
        assert result["slides"][0]["slide_number"] == 2
        assert result["slides"][1]["slide_number"] == 3
        assert result["slides"][2]["slide_number"] == 4

    @pytest.mark.asyncio
    async def test_read_notes_batch_all_slides(self, test_pptx_path):
        """Test reading notes from all slides."""
        result = await handle_read_notes_batch(
            {
                "pptx_path": test_pptx_path,
            }
        )

        assert result["success"] is True
        assert result["total_slides"] == 5
        assert len(result["slides"]) == 5

    @pytest.mark.asyncio
    async def test_read_notes_batch_both_parameters_error(self, test_pptx_path):
        """Test that providing both slide_numbers and slide_range raises an error."""
        result = await handle_read_notes_batch(
            {
                "pptx_path": test_pptx_path,
                "slide_numbers": [1, 2],
                "slide_range": "3-4",
            }
        )

        assert result["success"] is False
        assert "Cannot specify both" in result["error"]

    @pytest.mark.asyncio
    async def test_read_notes_batch_range_exceeds_slides(self, test_pptx_path):
        """Test that slide range exceeding presentation size is handled."""
        result = await handle_read_notes_batch(
            {
                "pptx_path": test_pptx_path,
                "slide_range": "1-100",
            }
        )

        assert result["success"] is False
        assert "Must be between 1 and 5" in result["error"]

    @pytest.mark.asyncio
    async def test_update_notes_batch_in_place(self, temp_pptx_path):
        """Test batch updating notes in-place."""
        updates = [
            {"slide_number": 1, "notes_text": "Updated notes for slide 1"},
            {"slide_number": 3, "notes_text": "Updated notes for slide 3"},
        ]

        result = await handle_update_notes_batch(
            {
                "pptx_path": temp_pptx_path,
                "updates": updates,
                "in_place": True,
            }
        )

        assert result["success"] is True
        assert result["updated_slides"] == 2
        assert result["in_place"] is True
        assert 1 in result["slides"]
        assert 3 in result["slides"]

        # Verify updates were applied
        verify_result = await handle_read_notes_batch(
            {
                "pptx_path": temp_pptx_path,
                "slide_numbers": [1, 3],
            }
        )

        assert "Updated notes for slide 1" in verify_result["slides"][0]["notes"]
        assert "Updated notes for slide 3" in verify_result["slides"][1]["notes"]

    @pytest.mark.asyncio
    async def test_update_notes_batch_new_file(self, temp_pptx_path):
        """Test batch updating notes to new file."""
        updates = [
            {"slide_number": 2, "notes_text": "New notes for slide 2"},
        ]

        output_path = str(Path(temp_pptx_path).with_suffix(".updated.pptx"))

        result = await handle_update_notes_batch(
            {
                "pptx_path": temp_pptx_path,
                "updates": updates,
                "in_place": False,
                "output_path": output_path,
            }
        )

        assert result["success"] is True
        assert result["in_place"] is False
        assert Path(result["output_path"]).exists()

        # Cleanup
        Path(result["output_path"]).unlink()

    @pytest.mark.asyncio
    async def test_process_notes_workflow(self, temp_pptx_path):
        """Test complete workflow with formatting."""
        notes_data = [
            {
                "slide_number": 1,
                "short_text": "Short summary for slide 1",
                "original_text": "Full detailed notes for slide 1 with more information",
            },
            {
                "slide_number": 2,
                "short_text": "Short summary for slide 2",
                "original_text": "Full detailed notes for slide 2 with more information",
            },
        ]

        result = await handle_process_notes_workflow(
            {
                "pptx_path": temp_pptx_path,
                "notes_data": notes_data,
                "in_place": True,
            }
        )

        assert result["success"] is True
        assert result["workflow"] == "process_notes_workflow"
        assert result["formatted_slides"] == 2

        # Verify formatted structure
        verify_result = await handle_read_notes_batch(
            {
                "pptx_path": temp_pptx_path,
                "slide_numbers": [1, 2],
            }
        )

        slide1_notes = verify_result["slides"][0]["notes"]
        assert "- Short version:" in slide1_notes
        assert "- Original:" in slide1_notes
        assert "Short summary for slide 1" in slide1_notes
        assert "Full detailed notes for slide 1" in slide1_notes

    @pytest.mark.asyncio
    async def test_process_notes_workflow_validation_error(self, temp_pptx_path):
        """Test workflow with invalid input."""
        notes_data = [
            {
                "slide_number": "invalid",  # Should be integer
                "short_text": "Short",
                "original_text": "Original",
            },
        ]

        result = await handle_process_notes_workflow(
            {
                "pptx_path": temp_pptx_path,
                "notes_data": notes_data,
                "in_place": True,
            }
        )

        assert result["success"] is False
        assert "error" in result


def run_tests():
    """Run all tests."""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_tests()
