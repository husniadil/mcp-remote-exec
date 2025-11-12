"""Tests for Path Validator"""

import os
import pytest
from mcp_remote_exec.data_access.path_validator import PathValidator, MSG_PATH_TRAVERSAL_ERROR
from mcp_remote_exec.data_access.exceptions import FileValidationError


class TestPathValidator:
    """Tests for PathValidator class"""

    def test_validate_path_empty(self):
        """Test validation fails for empty path"""
        with pytest.raises(FileValidationError, match="path cannot be empty"):
            PathValidator.validate_path("")

    def test_validate_path_whitespace_only(self):
        """Test validation fails for whitespace-only path"""
        with pytest.raises(FileValidationError, match="path cannot be empty"):
            PathValidator.validate_path("   ")

    def test_validate_path_traversal_simple(self):
        """Test validation fails for simple directory traversal"""
        with pytest.raises(FileValidationError, match="traversal"):
            PathValidator.validate_path("../etc/passwd")

    def test_validate_path_traversal_complex(self):
        """Test validation fails for complex directory traversal with relative parts"""
        # Note: os.path.normpath resolves /var/www/../../etc to /etc, which doesn't contain ..
        # So we test with a path that still contains .. after normalization
        with pytest.raises(FileValidationError, match="traversal"):
            PathValidator.validate_path("some/path/../../../etc/shadow")

    def test_validate_path_traversal_disabled(self):
        """Test validation passes when traversal check is disabled"""
        # Should not raise even with ..
        PathValidator.validate_path("../test", check_traversal=False)

    def test_validate_path_exists_check(self, tmp_path):
        """Test existence check for local files"""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        # Should pass for existing file
        PathValidator.validate_path(
            str(test_file), check_exists=True, path_type="local"
        )

        # Should fail for non-existing file
        with pytest.raises(FileValidationError, match="does not exist"):
            PathValidator.validate_path(
                str(tmp_path / "missing.txt"), check_exists=True, path_type="local"
            )

    def test_validate_path_custom_type(self):
        """Test custom path type in error messages"""
        with pytest.raises(FileValidationError, match="Container path"):
            PathValidator.validate_path("", path_type="container")

    def test_check_paths_for_traversal_all_valid(self):
        """Test multiple paths all valid"""
        is_valid, error = PathValidator.check_paths_for_traversal(
            "/var/www/html", "/tmp/upload", "/home/user/file.txt"
        )
        assert is_valid is True
        assert error is None

    def test_check_paths_for_traversal_one_invalid(self):
        """Test multiple paths with one invalid"""
        is_valid, error = PathValidator.check_paths_for_traversal(
            "/var/www/html", "../etc/passwd", "/home/user/file.txt"
        )
        assert is_valid is False
        assert error == MSG_PATH_TRAVERSAL_ERROR

    def test_check_paths_for_traversal_empty_list(self):
        """Test empty path list"""
        is_valid, error = PathValidator.check_paths_for_traversal()
        assert is_valid is True
        assert error is None

    def test_check_paths_for_traversal_single_path(self):
        """Test single path validation"""
        is_valid, error = PathValidator.check_paths_for_traversal("/var/www/html")
        assert is_valid is True
        assert error is None

        is_valid, error = PathValidator.check_paths_for_traversal("../etc/passwd")
        assert is_valid is False
        assert error == MSG_PATH_TRAVERSAL_ERROR

    def test_validate_path_absolute_path(self):
        """Test absolute paths are accepted"""
        PathValidator.validate_path("/absolute/path/to/file.txt")

    def test_validate_path_relative_path(self):
        """Test relative paths are accepted (without traversal)"""
        PathValidator.validate_path("relative/path/to/file.txt")

    def test_validate_path_current_directory(self):
        """Test current directory references are accepted"""
        PathValidator.validate_path("./file.txt")
        PathValidator.validate_path("./subdir/file.txt")

    def test_file_validation_error_attributes(self):
        """Test FileValidationError contains correct attributes"""
        try:
            PathValidator.validate_path("")
        except FileValidationError as e:
            assert e.file_path == ""
            assert e.reason == "empty_path"
            assert str(e)

    def test_file_validation_error_traversal_attributes(self):
        """Test FileValidationError for traversal contains correct attributes"""
        try:
            PathValidator.validate_path("../etc/passwd")
        except FileValidationError as e:
            assert e.file_path == "../etc/passwd"
            assert e.reason == "directory_traversal"
            assert MSG_PATH_TRAVERSAL_ERROR in str(e)
