"""Tests for custom exceptions"""

import pytest
from mcp_remote_exec.data_access.exceptions import (
    SSHConnectionError,
    AuthenticationError,
    CommandExecutionError,
    SFTPError,
    FileValidationError,
)


class TestSSHConnectionError:
    """Tests for SSHConnectionError"""

    def test_basic_exception(self):
        """Test basic exception creation"""
        error = SSHConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert error.host_name is None
        assert error.original_error is None

    def test_exception_with_host(self):
        """Test exception with host name"""
        error = SSHConnectionError("Connection failed", host_name="test.example.com")
        assert error.host_name == "test.example.com"

    def test_exception_with_original_error(self):
        """Test exception with original error"""
        original = ValueError("Original error")
        error = SSHConnectionError("Connection failed", original_error=original)
        assert error.original_error == original


class TestAuthenticationError:
    """Tests for AuthenticationError"""

    def test_basic_auth_error(self):
        """Test basic authentication error"""
        error = AuthenticationError("Auth failed")
        assert str(error) == "Auth failed"
        assert error.username is None

    def test_auth_error_with_username(self):
        """Test authentication error with username"""
        error = AuthenticationError(
            "Auth failed", host_name="test.example.com", username="testuser"
        )
        assert error.username == "testuser"
        assert error.host_name == "test.example.com"

    def test_auth_error_inheritance(self):
        """Test that AuthenticationError inherits from SSHConnectionError"""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, SSHConnectionError)


class TestCommandExecutionError:
    """Tests for CommandExecutionError"""

    def test_basic_command_error(self):
        """Test basic command execution error"""
        error = CommandExecutionError("Command failed")
        assert str(error) == "Command failed"
        assert error.command is None
        assert error.exit_code is None

    def test_command_error_with_details(self):
        """Test command error with details"""
        error = CommandExecutionError(
            "Command failed",
            host_name="test.example.com",
            command="ls -la",
            exit_code=1,
        )
        assert error.command == "ls -la"
        assert error.exit_code == 1
        assert error.host_name == "test.example.com"

    def test_command_error_inheritance(self):
        """Test that CommandExecutionError inherits from SSHConnectionError"""
        error = CommandExecutionError("Command failed")
        assert isinstance(error, SSHConnectionError)


class TestSFTPError:
    """Tests for SFTPError"""

    def test_basic_sftp_error(self):
        """Test basic SFTP error"""
        error = SFTPError("SFTP operation failed")
        assert str(error) == "SFTP operation failed"
        assert error.operation is None
        assert error.path is None

    def test_sftp_error_with_details(self):
        """Test SFTP error with details"""
        error = SFTPError(
            "SFTP upload failed",
            host_name="test.example.com",
            operation="upload",
            path="/remote/path/file.txt",
        )
        assert error.operation == "upload"
        assert error.path == "/remote/path/file.txt"
        assert error.host_name == "test.example.com"

    def test_sftp_error_inheritance(self):
        """Test that SFTPError inherits from SSHConnectionError"""
        error = SFTPError("SFTP failed")
        assert isinstance(error, SSHConnectionError)


class TestFileValidationError:
    """Tests for FileValidationError"""

    def test_basic_file_validation_error(self):
        """Test basic file validation error"""
        error = FileValidationError("File too large")
        assert str(error) == "File too large"
        assert error.file_path is None
        assert error.reason is None

    def test_file_validation_error_with_details(self):
        """Test file validation error with details"""
        error = FileValidationError(
            "File too large",
            file_path="/path/to/file.txt",
            reason="Exceeds maximum file size",
        )
        assert error.file_path == "/path/to/file.txt"
        assert error.reason == "Exceeds maximum file size"

    def test_file_validation_error_not_ssh_error(self):
        """Test that FileValidationError is not an SSHConnectionError"""
        error = FileValidationError("File invalid")
        assert not isinstance(error, SSHConnectionError)
        assert isinstance(error, Exception)
