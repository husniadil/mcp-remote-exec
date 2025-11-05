"""
Service Container for SSH MCP Remote Exec

Provides type-safe service dependency management.
"""

from dataclasses import dataclass, field
from typing import Any

from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager
from mcp_remote_exec.data_access.sftp_manager import SFTPManager
from mcp_remote_exec.services.command_service import CommandService
from mcp_remote_exec.services.file_transfer_service import FileTransferService
from mcp_remote_exec.services.output_formatter import OutputFormatter


@dataclass
class ServiceContainer:
    """Container for all application services with proper typing"""

    config: SSHConfig
    connection_manager: SSHConnectionManager
    sftp_manager: SFTPManager
    command_service: CommandService
    file_service: FileTransferService
    output_formatter: OutputFormatter
    plugin_services: dict[str, Any] = field(default_factory=dict)
