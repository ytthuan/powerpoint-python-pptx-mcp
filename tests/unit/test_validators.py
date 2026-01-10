import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.mcp_server.utils.validators import (
    _is_path_safe,
    _check_workspace_boundary,
    _check_file_size,
    validate_pptx_path,
    validate_slide_number,
    validate_position,
    validate_size,
    validate_text_input,
    parse_slide_range,
    validate_slide_numbers,
    validate_batch_updates,
)
from src.mcp_server.exceptions import (
    FileTooLargeError,
    InvalidPathError,
    InvalidSlideNumberError,
    ValidationError,
    WorkspaceBoundaryError,
    InputTooLargeError,
)


@pytest.fixture
def mock_config():
    with patch("src.mcp_server.utils.validators.get_config") as mock:
        config = MagicMock()
        config.security.enforce_workspace_boundary = True
        config.security.workspace_dirs = [Path("/tmp/workspace").resolve()]
        config.security.max_file_size = 10 * 1024 * 1024  # 10MB
        config.security.max_path_length = 255
        config.security.allowed_extensions = [".pptx"]
        config.security.max_text_length = 1000
        mock.return_value = config
        yield config


def test_is_path_safe():
    assert _is_path_safe(Path("/tmp/safe/path")) is True
    # In sandbox/normal OS, most paths can be resolved unless they are really crazy
    # but we can't easily trigger OSError/RuntimeError for resolve() without mocking


def test_check_workspace_boundary_within(mock_config):
    path = Path("/tmp/workspace/test.pptx")
    with patch.object(Path, "resolve", return_value=path.resolve()):
        # Should not raise
        _check_workspace_boundary(path)


def test_check_workspace_boundary_outside(mock_config):
    path = Path("/etc/passwd")
    with pytest.raises(WorkspaceBoundaryError):
        _check_workspace_boundary(path)


def test_check_workspace_boundary_disabled(mock_config):
    mock_config.security.enforce_workspace_boundary = False
    path = Path("/etc/passwd")
    # Should not raise
    _check_workspace_boundary(path)


def test_check_file_size_within(mock_config):
    path = MagicMock(spec=Path)
    path.exists.return_value = True
    path.stat.return_value.st_size = 5 * 1024 * 1024
    # Should not raise
    _check_file_size(path)


def test_check_file_size_exceeds(mock_config):
    path = MagicMock(spec=Path)
    path.exists.return_value = True
    path.stat.return_value.st_size = 15 * 1024 * 1024
    with pytest.raises(FileTooLargeError):
        _check_file_size(path)


def test_validate_pptx_path_success(mock_config):
    path_str = "/tmp/workspace/presentation.pptx"
    path_obj = Path(path_str)

    with (
        patch("src.mcp_server.utils.validators._is_path_safe", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "resolve", return_value=path_obj),
        patch("src.mcp_server.utils.validators._check_file_size"),
    ):

        result = validate_pptx_path(path_str)
        assert isinstance(result, Path)
        assert str(result).endswith("presentation.pptx")


def test_validate_pptx_path_invalid_extension(mock_config):
    path_str = "/tmp/workspace/presentation.txt"
    with (
        patch("src.mcp_server.utils.validators._is_path_safe", return_value=True),
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "resolve", return_value=Path(path_str)),
    ):

        with pytest.raises(InvalidPathError, match="Invalid file extension"):
            validate_pptx_path(path_str)


def test_validate_slide_number():
    assert validate_slide_number(1, 10) == 1
    assert validate_slide_number(10, 10) == 10
    with pytest.raises(InvalidSlideNumberError):
        validate_slide_number(0, 10)
    with pytest.raises(InvalidSlideNumberError):
        validate_slide_number(11, 10)
    with pytest.raises(ValidationError, match="integer"):
        validate_slide_number("1", 10)


def test_validate_position():
    assert validate_position({"x": 10.0, "y": 20.0}) == {"x": 10.0, "y": 20.0}
    assert validate_position(None) == {"x": 0.0, "y": 0.0}
    assert validate_position({"x": 10}) == {"x": 10.0, "y": 0.0}
    with pytest.raises(ValueError, match="dictionary"):
        validate_position([10, 20])
    with pytest.raises(ValueError, match="numbers"):
        validate_position({"x": "10"})


def test_validate_size():
    assert validate_size({"width": 100.0, "height": 200.0}) == {"width": 100.0, "height": 200.0}
    assert validate_size(None) == {"width": 100.0, "height": 100.0}
    with pytest.raises(ValueError, match="positive"):
        validate_size({"width": 0, "height": 100})


def test_validate_text_input(mock_config):
    assert validate_text_input("hello") == "hello"
    assert validate_text_input("a" * 1000) == "a" * 1000
    with pytest.raises(InputTooLargeError):
        validate_text_input("a" * 1001)
    with pytest.raises(ValidationError, match="string"):
        validate_text_input(123)


def test_parse_slide_range():
    assert parse_slide_range("1-5") == [1, 2, 3, 4, 5]
    assert parse_slide_range(" 1 - 3 ") == [1, 2, 3]
    with pytest.raises(ValueError, match="format"):
        parse_slide_range("1:5")
    with pytest.raises(ValueError, match="numbers"):
        parse_slide_range("a-b")
    with pytest.raises(ValueError, match="must be >= start"):
        parse_slide_range("5-1")
    with pytest.raises(ValueError, match="must be >= 1"):
        parse_slide_range("0-5")


def test_validate_slide_numbers():
    assert validate_slide_numbers([1, 2, 3], 10) == [1, 2, 3]
    with pytest.raises(ValueError, match="empty"):
        validate_slide_numbers([], 10)
    with pytest.raises(ValueError, match="integers"):
        validate_slide_numbers([1, "2"], 10)


def test_validate_batch_updates():
    updates = [
        {"slide_number": 1, "notes_text": "hello"},
        {"slide_number": 2, "notes_text": "world"},
    ]
    assert validate_batch_updates(updates, 10) == updates

    with pytest.raises(ValueError, match="empty"):
        validate_batch_updates([], 10)
    with pytest.raises(ValueError, match="missing required field 'slide_number'"):
        validate_batch_updates([{"notes_text": "hello"}], 10)
    with pytest.raises(ValueError, match="notes_text must be string"):
        validate_batch_updates([{"slide_number": 1, "notes_text": 123}], 10)
