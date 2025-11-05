"""
Data Access Layer for SSH MCP Remote Exec

Provides SSH connection management, SFTP operations, and low-level
interaction with remote servers.
"""

from mcp_remote_exec.data_access.ssh_connection_manager import (
    SSHConnectionManager,
    ExecutionResult,
)
from mcp_remote_exec.data_access.sftp_manager import SFTPManager, FileTransferResult
from mcp_remote_exec.data_access.exceptions import (
    SSHConnectionError,
    SFTPError,
    AuthenticationError,
    CommandExecutionError,
    FileValidationError,
)

__all__ = [
    "SSHConnectionManager",
    "SFTPManager",
    "ExecutionResult",
    "FileTransferResult",
    "SSHConnectionError",
    "SFTPError",
    "AuthenticationError",
    "CommandExecutionError",
    "FileValidationError",
]
