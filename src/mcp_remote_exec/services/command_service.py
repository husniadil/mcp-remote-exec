"""
Command Service for SSH MCP Remote Exec

Provides business logic for SSH command execution.
"""

import logging
from datetime import datetime

from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager
from mcp_remote_exec.data_access.exceptions import (
    CommandExecutionError,
    AuthenticationError,
    SSHConnectionError,
)
from mcp_remote_exec.services.output_formatter import OutputFormatter

_log = logging.getLogger(__name__)


class CommandService:
    """Provides business logic for SSH command execution"""

    def __init__(self, connection_manager: SSHConnectionManager, config: SSHConfig):
        """Initialize command service with dependencies"""
        self.connection_manager = connection_manager
        self.config = config
        self.output_formatter = OutputFormatter(config)

    def execute_command(
        self,
        command: str = "",
        timeout: int = 30,
        response_format: str = "text",
    ) -> str:
        """Execute SSH command with formatting.

        Args:
            command: Bash command to execute (already validated by Pydantic in presentation layer)
            timeout: Command timeout in seconds (default: 30, clamped to 1-300 based on config)
            response_format: Output format - "text" or "json" (case-insensitive)

        Returns:
            Formatted command output with execution metadata

        Note: Input validation (command length, timeout range) is handled by Pydantic models
        in the presentation layer before reaching this service method.
        """

        # Execute command
        try:
            host_config = self.config.get_host()
            _log.debug(f"Executing command on {host_config.name}: {command[:100]}")

            execution_result = self.connection_manager.execute_command(command, timeout)

            # Step 3: Format result
            formatted_result = self.output_formatter.format_command_output(
                execution_result, response_format
            )

            # Step 4: Add execution metadata
            metadata = [
                "\n\n=== EXECUTION METADATA ===",
                f"Host: {host_config.name} ({host_config.host}:{host_config.port})",
                f"User: {host_config.username}",
                f"Timestamp: {datetime.now().isoformat()}",
            ]

            formatted_result.content += "\n".join(metadata)

            return formatted_result.content

        except AuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            context = f"Command: {command}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content
        except CommandExecutionError as e:
            error_msg = f"Command execution failed: {str(e)}"
            context = f"Command: {command}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content
        except SSHConnectionError as e:
            error_msg = f"SSH connection error: {str(e)}"
            context = f"Command: {command}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            context = f"Command: {command}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content
