"""
MCP Tools for SSH MCP Remote Exec

Provides tools for SSH command execution and file transfers.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP
from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager
from mcp_remote_exec.data_access.sftp_manager import SFTPManager
from mcp_remote_exec.services.command_service import CommandService
from mcp_remote_exec.services.file_transfer_service import FileTransferService
from mcp_remote_exec.services.output_formatter import OutputFormatter
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.presentation.request_models import (
    ResponseFormat,
    SSHExecCommandInput,
    SSHUploadFileInput,
    SSHDownloadFileInput,
)

_log = logging.getLogger(__name__)

# Global application context for tool access
_app_context: ServiceContainer | None = None


def _initialize_services() -> ServiceContainer:
    """Initialize services on first use"""
    global _app_context
    if _app_context is not None:
        return _app_context

    _log.info("Initializing SSH MCP Remote Exec...")

    # Load configuration
    config = SSHConfig()

    # Validate configuration
    _, error = config.validate()
    if error:
        _log.error(f"Configuration validation failed: {error}")
        raise ValueError(error)

    _log.info(f"Configuration validated. Host: {config.get_host().name}")

    # Initialize Data Access Layer
    connection_manager = SSHConnectionManager(config)
    sftp_manager = SFTPManager(connection_manager)

    # Initialize Service Layer
    command_service = CommandService(connection_manager, config)
    file_service = FileTransferService(sftp_manager, config)
    output_formatter = OutputFormatter(config)

    # Store in application context
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
    activated_plugins = plugin_registry.discover_and_register(mcp, _app_context)

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
        _register_ssh_file_transfer_tools()

    _log.info("SSH MCP Remote Exec ready!")

    if activated_plugins:
        _log.info(f"Activated plugins: {', '.join(activated_plugins)}")
    else:
        _log.info("No plugins activated")

    return _app_context


def get_services() -> ServiceContainer:
    """Get service instances from global application context"""
    global _app_context
    if _app_context is None:
        return _initialize_services()
    return _app_context


# Create FastMCP server (stdio mode, no app_lifespan)
mcp = FastMCP("mcp_remote_exec")


# ============================================================================
# Core MCP Tools
# ============================================================================


@mcp.tool(name="ssh_exec_command")
async def ssh_exec_command(
    command: Annotated[
        str, "Bash command to execute on the remote server (required)"
    ] = "",
    timeout: Annotated[int, "Command timeout in seconds (1-300, default: 30)"] = 30,
    response_format: Annotated[
        str,
        "Output format: 'text' for human-readable or 'json' for structured data",
    ] = "text",
) -> str:
    """Execute a bash command on your remote SSH server.

    Use this tool to run commands on your configured Linux/Unix server for:
    - System administration (checking disk space, memory usage)
    - Service management (starting/stopping services)
    - File operations (listing files, reading logs)
    - Software management (installing packages, updates)
    - System diagnostics (checking system status)

    Args:
        command: Bash command to execute (required)
        timeout: Command timeout in seconds (default: 30, max: 300)
        response_format: Output format - 'text' for human-readable or 'json' for structured data

    Returns:
        Formatted command output with execution metadata
    """
    try:
        # Validate command is not empty (required parameter)
        if not command or not command.strip():
            return "[ERROR] Input validation error: 'command' parameter is required and cannot be empty"

        # Validate input using Pydantic model
        input_data = SSHExecCommandInput(
            command=command,
            timeout=timeout,
            response_format=ResponseFormat(response_format.lower()),
        )

        services = get_services()

        result = services.command_service.execute_command(
            command=input_data.command,
            timeout=input_data.timeout,
            response_format=input_data.response_format.value,
        )

        return result

    except ValueError as e:
        return f"[ERROR] Input validation error: {str(e)}"
    except Exception as e:
        return f"[ERROR] Unexpected error: {str(e)}"


def _register_ssh_file_transfer_tools() -> None:
    """Register SSH file transfer tools (upload/download)"""

    @mcp.tool(name="ssh_upload_file")
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
            # Validate required parameters are not empty
            if not local_path or not local_path.strip():
                return "[ERROR] Input validation error: 'local_path' parameter is required and cannot be empty"
            if not remote_path or not remote_path.strip():
                return "[ERROR] Input validation error: 'remote_path' parameter is required and cannot be empty"

            # Validate input
            input_data = SSHUploadFileInput(
                local_path=local_path,
                remote_path=remote_path,
                permissions=permissions,
                overwrite=overwrite,
            )

            services = get_services()

            result = services.file_service.upload_file(
                local_path=input_data.local_path,
                remote_path=input_data.remote_path,
                permissions=input_data.permissions,
                overwrite=input_data.overwrite,
            )

            return result

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"

    @mcp.tool(name="ssh_download_file")
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
            # Validate required parameters are not empty
            if not remote_path or not remote_path.strip():
                return "[ERROR] Input validation error: 'remote_path' parameter is required and cannot be empty"
            if not local_path or not local_path.strip():
                return "[ERROR] Input validation error: 'local_path' parameter is required and cannot be empty"

            # Validate input
            input_data = SSHDownloadFileInput(
                remote_path=remote_path, local_path=local_path, overwrite=overwrite
            )

            services = get_services()

            result = services.file_service.download_file(
                remote_path=input_data.remote_path,
                local_path=input_data.local_path,
                overwrite=input_data.overwrite,
            )

            return result

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"
