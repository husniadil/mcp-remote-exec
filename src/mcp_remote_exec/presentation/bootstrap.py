"""
Bootstrap Module for SSH MCP Remote Exec

Composition Root: This module is responsible for initializing all application layers
and wiring dependencies together. It's the only module that should import from all
layers (Config, Data Access, Services, Presentation).

This separation allows the presentation layer (mcp_tools.py) to remain clean and
only depend on services, while the composition root handles all the wiring.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP

from mcp_remote_exec.config.exceptions import ConfigError
from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager
from mcp_remote_exec.data_access.sftp_manager import SFTPManager
from mcp_remote_exec.services.command_service import CommandService
from mcp_remote_exec.services.file_transfer_service import FileTransferService
from mcp_remote_exec.services.output_formatter import OutputFormatter
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.presentation.models import (
    SSHUploadFileInput,
    SSHDownloadFileInput,
)

_log = logging.getLogger(__name__)

# Global application context
_app_context: ServiceContainer | None = None


def initialize(mcp_server: FastMCP) -> ServiceContainer:
    """
    Initialize all application layers and wire dependencies.

    This is the composition root where all layers come together. It's responsible
    for creating instances of config, data access, services, and presentation
    components, then wiring them together into a ServiceContainer.

    Args:
        mcp_server: The FastMCP server instance to register tools with

    Returns:
        ServiceContainer with all initialized services and configuration

    Raises:
        ConfigError: If configuration validation fails
    """
    global _app_context
    if _app_context is not None:
        return _app_context

    _log.info("Initializing SSH MCP Remote Exec...")

    # Load and validate configuration (Layer 1: Config)
    config = SSHConfig()
    _, error = config.validate()
    if error:
        _log.error(f"Configuration validation failed: {error}")
        raise ConfigError(error)

    _log.info(f"Configuration validated. Host: {config.get_host().name}")

    # Initialize Data Access Layer (Layer 2)
    connection_manager = SSHConnectionManager(config)
    sftp_manager = SFTPManager(connection_manager)

    # Initialize Service Layer (Layer 3)
    command_service = CommandService(connection_manager, config)
    file_service = FileTransferService(sftp_manager, config)
    output_formatter = OutputFormatter(config)

    # Create Service Container (Layer 4: Presentation)
    _app_context = ServiceContainer(
        config=config,
        connection_manager=connection_manager,
        sftp_manager=sftp_manager,
        command_service=command_service,
        file_service=file_service,
        output_formatter=output_formatter,
    )

    # Initialize and register plugins
    from mcp_remote_exec.plugins.registry import PluginRegistry

    plugin_registry = PluginRegistry()
    activated_plugins = plugin_registry.discover_and_register(mcp_server, _app_context)

    # Store activated plugins in context for later reference
    _app_context.plugin_services["_activated_plugins"] = activated_plugins

    # Register SSH file transfer tools conditionally
    # If ImageKit plugin is enabled, skip SSH file transfer tools
    imagekit_enabled = "imagekit" in _app_context.enabled_plugins
    if imagekit_enabled:
        _log.warning(
            "SSH file transfer tools (ssh_upload_file, ssh_download_file) NOT registered - "
            "ImageKit plugin provides alternative file transfer interface"
        )
    else:
        _log.info(
            "Registering SSH file transfer tools (ssh_upload_file, ssh_download_file)"
        )
        _register_ssh_file_transfer_tools(mcp_server)

    _log.info("SSH MCP Remote Exec ready!")

    if activated_plugins:
        _log.info(f"Activated plugins: {', '.join(activated_plugins)}")
    else:
        _log.info("No plugins activated")

    return _app_context


def get_container() -> ServiceContainer:
    """
    Get the global service container.

    Returns:
        The initialized ServiceContainer

    Raises:
        RuntimeError: If called before initialize()
    """
    if _app_context is None:
        raise RuntimeError(
            "Application not initialized. Call bootstrap.initialize() first."
        )
    return _app_context


def _register_ssh_file_transfer_tools(mcp_server: FastMCP) -> None:
    """
    Register SSH file transfer tools (upload/download).

    This function is called conditionally - only if ImageKit plugin is not enabled.
    ImageKit provides its own file transfer mechanism, so these tools would be redundant.

    Args:
        mcp_server: The FastMCP server instance to register tools with
    """

    @mcp_server.tool(name="ssh_upload_file")
    async def ssh_upload_file(
        local_path: Annotated[
            str, "Local file path to upload - absolute or relative (required)"
        ] = "",
        remote_path: Annotated[
            str, "Remote destination path on your SSH server (required)"
        ] = "",
        permissions: Annotated[
            int | None,
            "File permissions as octal value. Specify as decimal int representing octal notation (e.g., 644 for 0o644/rw-r--r--, 755 for 0o755/rwxr-xr-x). Optional.",
        ] = None,
        overwrite: Annotated[
            bool, "Overwrite existing remote files (default: False)"
        ] = False,
    ) -> str:
        """Upload a file to your remote SSH server via SFTP.

        Use this tool to transfer files to your configured server for:
        - Deploying configuration files (nginx.conf, app.conf)
        - Uploading scripts (install.sh, backup.sh)
        - Transferring data files (backups, logs)
        - Installing software packages

        Args:
            local_path: Local file path to upload - absolute or relative (required)
            remote_path: Remote destination path on your SSH server (required)
            permissions: File permissions as octal value. Specify as decimal int representing octal notation (e.g., 644 for 0o644/rw-r--r--, 755 for 0o755/rwxr-xr-x). Optional, defaults to server's umask.
            overwrite: Overwrite existing files (default: False, will fail if file exists)

        Returns:
            Transfer result with metadata (bytes transferred, speed, etc.)
        """
        try:
            # Validate input
            input_data = SSHUploadFileInput(
                local_path=local_path,
                remote_path=remote_path,
                permissions=permissions,
                overwrite=overwrite,
            )

            container = get_container()

            result = container.file_service.upload_file(
                local_path=input_data.local_path,
                remote_path=input_data.remote_path,
                permissions=input_data.permissions,
                overwrite=input_data.overwrite,
            )

            return result

        except ValueError as e:
            container = get_container()
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            container = get_container()
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp_server.tool(name="ssh_download_file")
    async def ssh_download_file(
        remote_path: Annotated[
            str, "Remote file path on your SSH server to download (required)"
        ] = "",
        local_path: Annotated[
            str, "Local destination file path - absolute or relative (required)"
        ] = "",
        overwrite: Annotated[
            bool,
            "Overwrite existing local files (default: False, will fail if file exists)",
        ] = False,
    ) -> str:
        """Download a file from your remote SSH server via SFTP.

        Use this tool to transfer files from your configured server:
        - Download log files (/var/log/app.log, /var/log/nginx/access.log)
        - Retrieving configuration files (/etc/nginx/nginx.conf, /etc/hosts)
        - Getting data files (database exports, backups)
        - Collecting system information (/proc/cpuinfo)

        Args:
            remote_path: Remote file path on your SSH server to download (required)
            local_path: Local destination path - absolute or relative (required)
            overwrite: Overwrite existing local files (default: False, will fail if file exists)

        Returns:
            Transfer result with metadata (bytes transferred, speed, etc.)
        """
        try:
            # Validate input
            input_data = SSHDownloadFileInput(
                remote_path=remote_path, local_path=local_path, overwrite=overwrite
            )

            container = get_container()

            result = container.file_service.download_file(
                remote_path=input_data.remote_path,
                local_path=input_data.local_path,
                overwrite=input_data.overwrite,
            )

            return result

        except ValueError as e:
            container = get_container()
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            container = get_container()
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content
