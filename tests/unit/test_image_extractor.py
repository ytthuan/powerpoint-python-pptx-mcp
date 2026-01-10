import pytest
import io
import base64
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.mcp_server.core.image_extractor import (
    extract_images_from_pptx,
    extract_image_as_base64,
    extract_slide_images,
)

@patch("src.mcp_server.core.image_extractor.validate_pptx_path")
@patch("zipfile.ZipFile")
@patch("PIL.Image.open")
def test_extract_images_from_pptx(mock_image_open, mock_zip_class, mock_validate_path):
    mock_validate_path.return_value = Path("test.pptx")
    mock_zip = mock_zip_class.return_value.__enter__.return_value
    
    # Mock image file in zip
    item = MagicMock()
    item.filename = "ppt/media/image1.png"
    mock_zip.infolist.return_value = [item]
    mock_zip.read.return_value = b"fake image data"
    
    # Mock PIL Image
    mock_img = MagicMock()
    mock_img.size = (100, 200)
    mock_img.format = "PNG"
    mock_image_open.return_value = mock_img
    
    result = extract_images_from_pptx("test.pptx")
    
    assert len(result) == 1
    assert result[0]["filename"] == "image1.png"
    assert result[0]["width"] == 100
    assert result[0]["height"] == 200
    assert result[0]["format"] == "PNG"

@patch("src.mcp_server.core.image_extractor.validate_pptx_path")
@patch("zipfile.ZipFile")
def test_extract_image_as_base64(mock_zip_class, mock_validate_path):
    mock_validate_path.return_value = Path("test.pptx")
    mock_zip = mock_zip_class.return_value.__enter__.return_value
    
    mock_zip.read.return_value = b"hello"
    
    result = extract_image_as_base64("test.pptx", "ppt/media/image1.png")
    
    expected = base64.b64encode(b"hello").decode("utf-8")
    assert result == expected

@patch("src.mcp_server.core.image_extractor.validate_pptx_path")
@patch("src.mcp_server.core.image_extractor.validate_slide_number")
@patch("pptx.Presentation")
@patch("PIL.Image.open")
def test_extract_slide_images(mock_image_open, mock_pres_class, mock_validate_slide, mock_validate_path):
    mock_validate_path.return_value = Path("test.pptx")
    
    mock_pres = mock_pres_class.return_value
    mock_slide = MagicMock()
    mock_pres.slides = [mock_slide]
    
    mock_shape = MagicMock()
    mock_shape.image.blob = b"image blob"
    mock_shape.shape_id = 10
    mock_shape.left = 0
    mock_shape.top = 0
    mock_shape.width = 100
    mock_shape.height = 100
    mock_slide.shapes = [mock_shape]
    
    # Mock PIL Image
    mock_img = MagicMock()
    mock_img.size = (50, 50)
    mock_img.format = "JPEG"
    mock_image_open.return_value = mock_img
    
    result = extract_slide_images("test.pptx", 1)
    
    assert len(result) == 1
    assert result[0]["shape_id"] == 10
    assert result[0]["image_width"] == 50
    assert result[0]["format"] == "JPEG"
