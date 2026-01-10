"""Unit tests for exception hierarchy module."""

from mcp_server.exceptions import (
    PPTXError,
    ValidationError,
    InvalidSlideNumberError,
    InvalidPathError,
    FileOperationError,
    PPTXFileNotFoundError,
    FileAccessError,
    FileTooLargeError,
    PresentationError,
    SlideNotFoundError,
    SecurityError,
    PathTraversalError,
    WorkspaceBoundaryError,
    ResourceError,
    OperationTimeoutError,
)


class TestPPTXError:
    """Tests for base PPTXError class."""

    def test_basic_creation(self):
        """Test creating a basic error."""
        error = PPTXError("Test message")
        assert str(error) == "Test message"
        assert error.message == "Test message"
        assert error.details == {}
        assert error.cause is None

    def test_with_details(self):
        """Test creating error with details."""
        details = {"key": "value", "number": 42}
        error = PPTXError("Test message", details=details)
        assert error.details == details

    def test_with_cause(self):
        """Test creating error with cause."""
        cause = ValueError("Original error")
        error = PPTXError("Test message", cause=cause)
        assert error.cause is cause

    def test_to_dict(self):
        """Test converting error to dictionary."""
        details = {"slide": 5}
        error = PPTXError("Test message", details=details)
        error_dict = error.to_dict()

        assert error_dict["error_type"] == "PPTXError"
        assert error_dict["message"] == "Test message"
        assert error_dict["details"] == details
        assert "cause" not in error_dict

    def test_to_dict_with_cause(self):
        """Test converting error with cause to dictionary."""
        cause = ValueError("Original error")
        error = PPTXError("Test message", cause=cause)
        error_dict = error.to_dict()

        assert "cause" in error_dict
        assert error_dict["cause"] == "Original error"


class TestValidationErrors:
    """Tests for validation error classes."""

    def test_validation_error(self):
        """Test generic ValidationError."""
        error = ValidationError("Invalid input")
        assert isinstance(error, PPTXError)
        assert error.message == "Invalid input"

    def test_invalid_slide_number_error(self):
        """Test InvalidSlideNumberError."""
        error = InvalidSlideNumberError(15, 10)
        assert isinstance(error, ValidationError)
        assert "15" in error.message
        assert "10" in error.message
        assert error.details["slide_number"] == 15
        assert error.details["max_slides"] == 10

    def test_invalid_path_error(self):
        """Test InvalidPathError."""
        error = InvalidPathError("/invalid/path", reason="Path not found")
        assert isinstance(error, ValidationError)
        assert "/invalid/path" in error.message
        assert "Path not found" in error.message
        assert error.details["path"] == "/invalid/path"


class TestFileOperationErrors:
    """Tests for file operation error classes."""

    def test_file_not_found_error(self):
        """Test PPTXFileNotFoundError."""
        error = PPTXFileNotFoundError("/path/to/file.pptx")
        assert isinstance(error, FileOperationError)
        assert "/path/to/file.pptx" in error.message
        assert error.details["file_path"] == "/path/to/file.pptx"

    def test_file_access_error(self):
        """Test FileAccessError."""
        error = FileAccessError("/path/to/file.pptx", reason="Permission denied")
        assert isinstance(error, FileOperationError)
        assert "/path/to/file.pptx" in error.message
        assert "Permission denied" in error.message

    def test_file_too_large_error(self):
        """Test FileTooLargeError."""
        error = FileTooLargeError("/path/to/file.pptx", 2000000000, 1000000000)
        assert isinstance(error, FileOperationError)
        assert error.details["file_path"] == "/path/to/file.pptx"
        assert error.details["size"] == 2000000000
        assert error.details["max_size"] == 1000000000


class TestPresentationErrors:
    """Tests for presentation error classes."""

    def test_slide_not_found_error(self):
        """Test SlideNotFoundError."""
        error = SlideNotFoundError(42)
        assert isinstance(error, PresentationError)
        assert "42" in error.message
        assert error.details["slide_number"] == 42


class TestSecurityErrors:
    """Tests for security error classes."""

    def test_path_traversal_error(self):
        """Test PathTraversalError."""
        error = PathTraversalError("../../etc/passwd")
        assert isinstance(error, SecurityError)
        assert "../../etc/passwd" in error.message
        assert error.details["path"] == "../../etc/passwd"

    def test_workspace_boundary_error(self):
        """Test WorkspaceBoundaryError."""
        error = WorkspaceBoundaryError("/forbidden/path", ["/allowed1", "/allowed2"])
        assert isinstance(error, SecurityError)
        assert "/forbidden/path" in error.message
        assert error.details["path"] == "/forbidden/path"
        assert error.details["allowed_dirs"] == ["/allowed1", "/allowed2"]


class TestResourceErrors:
    """Tests for resource error classes."""

    def test_operation_timeout_error(self):
        """Test OperationTimeoutError."""
        error = OperationTimeoutError("load_presentation", 300)
        assert isinstance(error, ResourceError)
        assert "load_presentation" in error.message
        assert "300" in error.message
        assert error.details["operation"] == "load_presentation"
        assert error.details["timeout"] == 300


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_all_inherit_from_pptx_error(self):
        """Test all custom errors inherit from PPTXError."""
        errors = [
            ValidationError("test"),
            FileOperationError("test"),
            PresentationError("test"),
            SecurityError("test"),
            ResourceError("test"),
        ]

        for error in errors:
            assert isinstance(error, PPTXError)
            assert isinstance(error, Exception)

    def test_specific_errors_inherit_from_base(self):
        """Test specific errors inherit from their base classes."""
        assert isinstance(InvalidSlideNumberError(1, 10), ValidationError)
        assert isinstance(PPTXFileNotFoundError("path"), FileOperationError)
        assert isinstance(SlideNotFoundError(1), PresentationError)
        assert isinstance(PathTraversalError("path"), SecurityError)
        assert isinstance(OperationTimeoutError("op", 10), ResourceError)
