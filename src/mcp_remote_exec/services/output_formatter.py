"""
Output Formatter for SSH MCP Remote Exec

Handles response formatting, output truncation, and result presentation
for SSH operations.
"""

import json
from dataclasses import dataclass

from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.constants import JSON_METADATA_OVERHEAD, MIN_OUTPUT_SPACE
from mcp_remote_exec.data_access.ssh_connection_manager import ExecutionResult
from mcp_remote_exec.data_access.sftp_manager import FileTransferResult


@dataclass
class FormattedResult:
    """Formatted operation result with metadata"""

    content: str  # The formatted output content (may be truncated)
    truncated: bool = False  # Whether the output was truncated due to size limits
    original_length: int | None = (
        None  # Original content length before truncation (None if not truncated)
    )
    format_type: str = "text"  # Output format type: "text" for human-readable, "json" for structured data


class OutputFormatter:
    """Handles output formatting and truncation"""

    def __init__(self, config: SSHConfig):
        """Initialize formatter with configuration"""
        self.config = config

    def format_command_output(
        self,
        result: ExecutionResult,
        format_type: str = "text",
        max_length: int | None = None,
    ) -> FormattedResult:
        """Format SSH command execution result.

        Args:
            result: Execution result from SSH command
            format_type: Output format - "text" or "json" (default: "text")
            max_length: Maximum output length, uses config limit if None

        Returns:
            FormattedResult with content, truncation status, and metadata
        """

        # Use configured limit if not specified
        if max_length is None:
            max_length = self.config.security.character_limit

        if format_type.lower() == "json":
            return self._format_command_json(result, max_length)
        else:
            return self._format_command_text(result, max_length)

    def _format_command_json(
        self, result: ExecutionResult, max_length: int
    ) -> FormattedResult:
        """Format command result as JSON with truncation"""

        # Calculate data length and allocate space
        stdout_len = len(result.stdout)
        stderr_len = len(result.stderr)
        total_len = stdout_len + stderr_len

        # Track truncation status
        stdout_truncated = False
        stderr_truncated = False
        final_stdout = result.stdout
        final_stderr = result.stderr

        if total_len > max_length:
            # Reserve space for JSON structure metadata
            available_space = max(max_length - JSON_METADATA_OVERHEAD, MIN_OUTPUT_SPACE)

            # Allocate space proportionally
            if total_len > 0:
                stdout_ratio = stdout_len / total_len
                stderr_ratio = stderr_len / total_len
                stdout_limit = int(available_space * stdout_ratio)
                stderr_limit = int(available_space * stderr_ratio)
            else:
                stdout_limit = available_space // 2
                stderr_limit = available_space // 2

            # Truncate content
            if stdout_len > stdout_limit:
                final_stdout = result.stdout[:stdout_limit]
                stdout_truncated = True

            if stderr_len > stderr_limit:
                final_stderr = result.stderr[:stderr_limit]
                stderr_truncated = True

        # Build JSON object
        json_result = {
            "success": result.exit_code == 0,
            "exit_code": result.exit_code,
            "stdout": final_stdout,
            "stderr": final_stderr,
            "command": result.command,
            "timeout_reached": result.timeout_reached,
        }

        # Add truncation metadata
        if stdout_truncated:
            json_result["stdout_truncated"] = True
            json_result["stdout_original_length"] = stdout_len

        if stderr_truncated:
            json_result["stderr_truncated"] = True
            json_result["stderr_original_length"] = stderr_len

        json_content = json.dumps(json_result, indent=2)

        return FormattedResult(
            content=json_content,
            truncated=stdout_truncated or stderr_truncated,
            original_length=total_len,
            format_type="json",
        )

    def _format_command_text(
        self, result: ExecutionResult, max_length: int
    ) -> FormattedResult:
        """Format command result as human-readable text"""

        # Build text output sections
        sections = []

        if result.stdout:
            sections.append(f"=== STDOUT ===\n{result.stdout}")

        if result.stderr:
            sections.append(f"=== STDERR ===\n{result.stderr}")

        # Add execution metadata
        metadata = [
            f"=== EXIT CODE: {result.exit_code} ===",
            f"Command: {result.command}",
        ]

        if result.timeout_reached:
            metadata.append("[WARNING] EXECUTION TIMED OUT")

        sections.append("\n".join(metadata))

        # Combine all sections
        full_output = "\n\n".join(sections)

        # Truncate if needed
        original_length = len(full_output)
        truncated = False

        if len(full_output) > max_length:
            truncated_output = full_output[:max_length]
            truncation_note = f"\n\n[OUTPUT TRUNCATED - showing first {max_length} of {original_length} characters]"
            full_output = truncated_output + truncation_note
            truncated = True

        return FormattedResult(
            content=full_output,
            truncated=truncated,
            original_length=original_length,
            format_type="text",
        )

    def format_file_transfer_result(
        self, result: FileTransferResult
    ) -> FormattedResult:
        """Format file transfer operation result.

        Args:
            result: File transfer result with operation details

        Returns:
            FormattedResult with transfer status and details
        """

        if result.success:
            sections = [
                f"[SUCCESS] File {result.operation.upper()} successful",
                f"Operation: {result.operation}",
                f"Local path: {result.local_path or 'N/A'}",
                f"Remote path: {result.remote_path or 'N/A'}",
                f"Bytes transferred: {result.bytes_transferred}",
            ]

            if result.transfer_speed > 0:
                sections.append(f"Transfer speed: {result.transfer_speed:.0f} bytes/s")

            content = "\n".join(sections)
        else:
            content = (
                f"[FAILED] File {result.operation.upper()} failed: {result.message}"
            )

        return FormattedResult(content=content, truncated=False, format_type="text")

    def format_error_result(
        self, error_message: str, context: str = ""
    ) -> FormattedResult:
        """Format error message with optional context"""

        content = f"[ERROR] {error_message}"
        if context:
            content += f"\n\nContext: {context}"

        return FormattedResult(content=content, truncated=False, format_type="text")

    def truncate_output(
        self, output: str, max_length: int | None = None
    ) -> FormattedResult:
        """Truncate output to specified maximum length.

        Args:
            output: Text output to truncate
            max_length: Maximum length, uses config limit if None

        Returns:
            FormattedResult with truncated content and metadata
        """

        if max_length is None:
            max_length = self.config.security.character_limit

        original_length = len(output)
        truncated = False

        if len(output) > max_length:
            truncated_output = output[:max_length]
            truncation_note = f"\n\n[TRUNCATED - showing first {max_length} of {original_length} characters]"
            output = truncated_output + truncation_note
            truncated = True

        return FormattedResult(
            content=output,
            truncated=truncated,
            original_length=original_length,
            format_type="text",
        )

    def get_summary_stats(self, result: FormattedResult) -> dict[str, int | str | bool]:
        """Get summary statistics about the formatted result"""

        return {
            "length": len(result.content),
            "truncated": result.truncated,
            "original_length": result.original_length or len(result.content),
            "format_type": result.format_type,
            "saved_characters": (result.original_length or 0) - len(result.content)
            if result.truncated
            else 0,
        }
