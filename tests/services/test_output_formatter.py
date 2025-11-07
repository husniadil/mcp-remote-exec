"""Tests for Output Formatter"""

import pytest
from mcp_remote_exec.services.output_formatter import OutputFormatter, FormattedResult
from mcp_remote_exec.data_access.ssh_connection_manager import ExecutionResult
from mcp_remote_exec.data_access.sftp_manager import FileTransferResult


class TestFormattedResult:
    """Tests for FormattedResult dataclass"""

    def test_formatted_result_defaults(self):
        """Test FormattedResult with default values"""
        result = FormattedResult(content="test output")
        assert result.content == "test output"
        assert result.truncated is False
        assert result.original_length is None
        assert result.format_type == "text"

    def test_formatted_result_custom_values(self):
        """Test FormattedResult with custom values"""
        result = FormattedResult(
            content="truncated",
            truncated=True,
            original_length=1000,
            format_type="json",
        )
        assert result.truncated is True
        assert result.original_length == 1000
        assert result.format_type == "json"


class TestOutputFormatter:
    """Tests for OutputFormatter class"""

    def test_formatter_initialization(self, mock_ssh_config):
        """Test formatter initialization"""
        formatter = OutputFormatter(mock_ssh_config)
        assert formatter.config == mock_ssh_config

    def test_format_command_text_success(self, mock_ssh_config):
        """Test formatting successful command output as text"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=0,
            stdout="Hello World",
            stderr="",
            command="echo 'Hello World'",
        )

        result = formatter.format_command_output(exec_result, format_type="text")

        assert result.format_type == "text"
        assert "Hello World" in result.content
        assert "EXIT CODE: 0" in result.content
        assert "echo 'Hello World'" in result.content
        assert result.truncated is False

    def test_format_command_text_with_stderr(self, mock_ssh_config):
        """Test formatting command output with stderr"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=1,
            stdout="Output",
            stderr="Error occurred",
            command="test command",
        )

        result = formatter.format_command_output(exec_result, format_type="text")

        assert "STDOUT" in result.content
        assert "Output" in result.content
        assert "STDERR" in result.content
        assert "Error occurred" in result.content
        assert "EXIT CODE: 1" in result.content

    def test_format_command_text_timeout(self, mock_ssh_config):
        """Test formatting command output with timeout"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=124,
            stdout="",
            stderr="",
            command="long command",
            timeout_reached=True,
        )

        result = formatter.format_command_output(exec_result, format_type="text")

        assert "EXECUTION TIMED OUT" in result.content

    def test_format_command_text_truncation(self, mock_ssh_config):
        """Test text output truncation"""
        formatter = OutputFormatter(mock_ssh_config)
        long_output = "A" * 30000
        exec_result = ExecutionResult(
            exit_code=0,
            stdout=long_output,
            stderr="",
            command="test",
        )

        result = formatter.format_command_output(exec_result, format_type="text")

        assert result.truncated is True
        assert result.original_length > mock_ssh_config.security.character_limit
        assert len(result.content) <= mock_ssh_config.security.character_limit + 200
        assert "OUTPUT TRUNCATED" in result.content

    def test_format_command_json_success(self, mock_ssh_config):
        """Test formatting command output as JSON"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=0,
            stdout="Success",
            stderr="",
            command="test command",
        )

        result = formatter.format_command_output(exec_result, format_type="json")

        assert result.format_type == "json"
        assert '"success": true' in result.content
        assert '"exit_code": 0' in result.content
        assert '"stdout": "Success"' in result.content
        assert '"command": "test command"' in result.content

    def test_format_command_json_with_failure(self, mock_ssh_config):
        """Test formatting failed command as JSON"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=1,
            stdout="",
            stderr="Error message",
            command="failing command",
        )

        result = formatter.format_command_output(exec_result, format_type="json")

        assert '"success": false' in result.content
        assert '"exit_code": 1' in result.content
        assert '"stderr": "Error message"' in result.content

    def test_format_command_json_truncation(self, mock_ssh_config):
        """Test JSON output truncation"""
        formatter = OutputFormatter(mock_ssh_config)
        long_stdout = "A" * 20000
        long_stderr = "B" * 20000
        exec_result = ExecutionResult(
            exit_code=0,
            stdout=long_stdout,
            stderr=long_stderr,
            command="test",
        )

        result = formatter.format_command_output(exec_result, format_type="json")

        assert result.truncated is True
        assert "stdout_truncated" in result.content
        assert "stderr_truncated" in result.content
        assert "stdout_original_length" in result.content
        assert "stderr_original_length" in result.content

    def test_format_file_transfer_success(self, mock_ssh_config):
        """Test formatting successful file transfer"""
        formatter = OutputFormatter(mock_ssh_config)
        transfer_result = FileTransferResult(
            success=True,
            message="Transfer complete",
            bytes_transferred=1024,
            transfer_speed=512.5,
            local_path="/local/file.txt",
            remote_path="/remote/file.txt",
            operation="upload",
        )

        result = formatter.format_file_transfer_result(transfer_result)

        assert "[SUCCESS]" in result.content
        assert "UPLOAD" in result.content
        assert "/local/file.txt" in result.content
        assert "/remote/file.txt" in result.content
        assert "1024" in result.content
        assert "512" in result.content

    def test_format_file_transfer_failure(self, mock_ssh_config):
        """Test formatting failed file transfer"""
        formatter = OutputFormatter(mock_ssh_config)
        transfer_result = FileTransferResult(
            success=False,
            message="File not found",
            operation="download",
        )

        result = formatter.format_file_transfer_result(transfer_result)

        assert "[FAILED]" in result.content
        assert "DOWNLOAD" in result.content
        assert "File not found" in result.content

    def test_format_error_result(self, mock_ssh_config):
        """Test formatting error result"""
        formatter = OutputFormatter(mock_ssh_config)
        result = formatter.format_error_result("Something went wrong")

        assert "[ERROR]" in result.content
        assert "Something went wrong" in result.content

    def test_format_error_result_with_context(self, mock_ssh_config):
        """Test formatting error result with context"""
        formatter = OutputFormatter(mock_ssh_config)
        result = formatter.format_error_result(
            "Connection failed", context="Host unreachable"
        )

        assert "[ERROR]" in result.content
        assert "Connection failed" in result.content
        assert "Context: Host unreachable" in result.content

    def test_truncate_output_no_truncation(self, mock_ssh_config):
        """Test truncation when output is within limit"""
        formatter = OutputFormatter(mock_ssh_config)
        short_output = "Short output"

        result = formatter.truncate_output(short_output)

        assert result.content == short_output
        assert result.truncated is False
        assert result.original_length == len(short_output)

    def test_truncate_output_with_truncation(self, mock_ssh_config):
        """Test truncation when output exceeds limit"""
        formatter = OutputFormatter(mock_ssh_config)
        long_output = "X" * 30000

        result = formatter.truncate_output(long_output)

        assert result.truncated is True
        assert len(result.content) < len(long_output)
        assert "TRUNCATED" in result.content
        assert result.original_length == 30000

    def test_truncate_output_custom_limit(self, mock_ssh_config):
        """Test truncation with custom limit"""
        formatter = OutputFormatter(mock_ssh_config)
        output = "A" * 1000

        result = formatter.truncate_output(output, max_length=500)

        assert result.truncated is True
        assert result.original_length == 1000

    def test_get_summary_stats_not_truncated(self, mock_ssh_config):
        """Test summary stats for non-truncated result"""
        formatter = OutputFormatter(mock_ssh_config)
        result = FormattedResult(content="test", truncated=False, format_type="text")

        stats = formatter.get_summary_stats(result)

        assert stats["length"] == 4
        assert stats["truncated"] is False
        assert stats["format_type"] == "text"
        assert stats["saved_characters"] == 0

    def test_get_summary_stats_truncated(self, mock_ssh_config):
        """Test summary stats for truncated result"""
        formatter = OutputFormatter(mock_ssh_config)
        result = FormattedResult(
            content="truncated",
            truncated=True,
            original_length=1000,
            format_type="json",
        )

        stats = formatter.get_summary_stats(result)

        assert stats["length"] == 9
        assert stats["truncated"] is True
        assert stats["original_length"] == 1000
        assert stats["saved_characters"] == 991

    def test_format_command_empty_output(self, mock_ssh_config):
        """Test formatting command with no output"""
        formatter = OutputFormatter(mock_ssh_config)
        exec_result = ExecutionResult(
            exit_code=0,
            stdout="",
            stderr="",
            command="silent command",
        )

        result = formatter.format_command_output(exec_result, format_type="text")

        assert "EXIT CODE: 0" in result.content
        assert "silent command" in result.content
        assert "STDOUT" not in result.content
        assert "STDERR" not in result.content
