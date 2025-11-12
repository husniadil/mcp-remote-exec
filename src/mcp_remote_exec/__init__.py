"""
SSH MCP Remote Exec

A Model Context Protocol (MCP) server that provides SSH access to remote servers.
This allows AI assistants to execute commands, transfer files, and manage remote systems
through natural language interfaces.

Architecture (Layered, bottom-up):
- Layer 1: Configuration - SSH host setup, security settings, and configuration management
- Layer 2: Data Access - SSH connections, SFTP operations, and domain exceptions
- Layer 3: Services - Business logic, validation, and output formatting
- Layer 4: Presentation - FastMCP tools and request models for AI interfaces

Security Features:
- Risk acceptance validation (REQUIRED)
- Command safety classification
- File size and path validation
- Connection timeout management
- Comprehensive error handling

Installation:
    pip install -e .
    mcp-remote-exec

CLI Usage:
    mcp-remote-exec                    # stdio mode (Claude Desktop)
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mcp-remote-exec")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"

__description__ = "SSH MCP Remote Exec for remote server management"

# Package exports
from .config import SSHConfig, HostConfig, SecurityConfig
from .data_access import (
    SSHConnectionManager,
    SFTPManager,
    ExecutionResult,
    FileTransferResult,
    SSHConnectionError,
    SFTPError,
    AuthenticationError,
    CommandExecutionError,
    FileValidationError,
)
from .services import (
    CommandService,
    FileTransferService,
    OutputFormatter,
    FormattedResult,
)
from .presentation import (
    ResponseFormat,
    SSHExecCommandInput,
    SSHUploadFileInput,
    SSHDownloadFileInput,
    ServiceContainer,
)

__all__ = [
    "SSHConfig",
    "HostConfig",
    "SecurityConfig",
    "SSHConnectionManager",
    "SFTPManager",
    "ExecutionResult",
    "FileTransferResult",
    "SSHConnectionError",
    "SFTPError",
    "AuthenticationError",
    "CommandExecutionError",
    "FileValidationError",
    "CommandService",
    "FileTransferService",
    "OutputFormatter",
    "FormattedResult",
    "ResponseFormat",
    "SSHExecCommandInput",
    "SSHUploadFileInput",
    "SSHDownloadFileInput",
    "ServiceContainer",
]
