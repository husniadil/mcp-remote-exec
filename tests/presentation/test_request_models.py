"""Tests for Request Models"""

import pytest
from pydantic import ValidationError

from mcp_remote_exec.presentation.request_models import (
    ResponseFormat,
    SSHExecCommandInput,
    SSHUploadFileInput,
    SSHDownloadFileInput,
)


class TestResponseFormat:
    """Tests for ResponseFormat enum"""

    def test_response_format_text(self):
        """Test TEXT format value"""
        assert ResponseFormat.TEXT.value == "text"

    def test_response_format_json(self):
        """Test JSON format value"""
        assert ResponseFormat.JSON.value == "json"


class TestSSHExecCommandInput:
    """Tests for SSHExecCommandInput model"""

    def test_valid_command(self):
        """Test valid command input"""
        input_data = SSHExecCommandInput(
            command="ls -la",
            timeout=30,
            response_format=ResponseFormat.TEXT,
        )
        assert input_data.command == "ls -la"
        assert input_data.timeout == 30
        assert input_data.response_format == ResponseFormat.TEXT

    def test_command_too_long(self):
        """Test command exceeds max length"""
        long_command = "a" * 10001
        with pytest.raises(ValidationError):
            SSHExecCommandInput(command=long_command)

    def test_timeout_validation(self):
        """Test timeout boundary validation"""
        # Valid timeout
        input_data = SSHExecCommandInput(command="ls", timeout=150)
        assert input_data.timeout == 150

        # Timeout too high
        with pytest.raises(ValidationError):
            SSHExecCommandInput(command="ls", timeout=301)

        # Timeout too low
        with pytest.raises(ValidationError):
            SSHExecCommandInput(command="ls", timeout=0)


class TestSSHUploadFileInput:
    """Tests for SSHUploadFileInput model"""

    def test_valid_upload_input(self):
        """Test valid upload input"""
        input_data = SSHUploadFileInput(
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            permissions=644,
            overwrite=False,
        )
        assert input_data.local_path == "/local/file.txt"
        assert input_data.remote_path == "/remote/file.txt"
        assert input_data.permissions == 644
        assert input_data.overwrite is False

    def test_path_length_validation(self):
        """Test path length limits"""
        # Path too long
        long_path = "a" * 4097
        with pytest.raises(ValidationError):
            SSHUploadFileInput(local_path=long_path, remote_path="/remote/file.txt")

    def test_permissions_validation(self):
        """Test permissions octal validation"""
        # Valid permission
        input_data = SSHUploadFileInput(
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            permissions=755,
        )
        assert input_data.permissions == 755

        # Invalid octal digit (8)
        with pytest.raises(ValidationError):
            SSHUploadFileInput(
                local_path="/local/file.txt",
                remote_path="/remote/file.txt",
                permissions=888,
            )


class TestSSHDownloadFileInput:
    """Tests for SSHDownloadFileInput model"""

    def test_valid_download_input(self):
        """Test valid download input"""
        input_data = SSHDownloadFileInput(
            remote_path="/remote/file.txt",
            local_path="/local/file.txt",
            overwrite=True,
        )
        assert input_data.remote_path == "/remote/file.txt"
        assert input_data.local_path == "/local/file.txt"
        assert input_data.overwrite is True

    def test_path_validation(self):
        """Test path validation"""
        # Valid paths
        input_data = SSHDownloadFileInput(
            remote_path="/remote/file.txt", local_path="/local/file.txt"
        )
        assert input_data.remote_path == "/remote/file.txt"

        # Empty path
        with pytest.raises(ValidationError):
            SSHDownloadFileInput(remote_path="", local_path="/local/file.txt")
