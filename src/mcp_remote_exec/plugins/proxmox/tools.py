"""
MCP Tools for Proxmox Plugin

Registers Proxmox container management tools.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.proxmox.service import ProxmoxService
from mcp_remote_exec.plugins.proxmox.models import (
    ProxmoxContainerExecInput,
    ProxmoxListContainersInput,
    ProxmoxContainerStatusInput,
    ProxmoxContainerActionInput,
    ProxmoxDownloadFileInput,
    ProxmoxUploadFileInput,
)
from mcp_remote_exec.presentation.request_models import ResponseFormat

_log = logging.getLogger(__name__)


def register_proxmox_tools(mcp: FastMCP, container: ServiceContainer) -> None:
    """
    Register all Proxmox plugin tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        container: Service container with core services
    """
    # Get Proxmox service from plugin services
    proxmox_service_obj = container.plugin_services.get("proxmox")
    if not proxmox_service_obj or not isinstance(proxmox_service_obj, ProxmoxService):
        _log.error("Proxmox service not found in plugin services")
        return

    proxmox_service: ProxmoxService = proxmox_service_obj

    @mcp.tool(name="proxmox_container_exec_command")
    async def proxmox_container_exec_command(
        ctid: Annotated[int, "Container ID (100-999999999)"] = 100,
        command: Annotated[str, "Bash command to execute in the container"] = "",
        timeout: Annotated[int, "Command timeout in seconds (1-300, default: 30)"] = 30,
        response_format: Annotated[str, "Output format: 'text' or 'json'"] = "text",
    ) -> str:
        """Execute a bash command inside a Proxmox LXC container.

        This tool runs commands inside containers using 'pct exec'.
        It provides full access to the container's shell environment.

        Use cases:
        - System administration tasks (checking disk space, memory usage)
        - Software installation and updates
        - File operations (creating, reading, modifying files)
        - Service management (starting/stopping services)
        - Log inspection and debugging

        Args:
            ctid: Container ID (100-999999999)
            command: Bash command to execute
            timeout: Command timeout in seconds (default: 30, max: 300)
            response_format: Output format - 'text' or 'json'

        Returns:
            Command output in requested format

        Example:
            proxmox_container_exec_command(ctid=100, command="df -h")
            proxmox_container_exec_command(ctid=101, command="apt update", timeout=120)
        """
        try:
            # Validate and convert response_format string to enum
            input_data = ProxmoxContainerExecInput(
                ctid=ctid,
                command=command,
                timeout=timeout,
                response_format=ResponseFormat(response_format.lower()),
            )

            return proxmox_service.exec_in_container(
                ctid=input_data.ctid,
                command=input_data.command,
                timeout=input_data.timeout,
                response_format=input_data.response_format.value,
            )

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp.tool(name="proxmox_list_containers")
    async def proxmox_list_containers(
        response_format: Annotated[str, "Output format: 'json' or 'text'"] = "text",
    ) -> str:
        """List all LXC containers on the Proxmox host.

        This tool retrieves information about all containers including their
        VM ID, status (running/stopped), and name.

        Args:
            response_format: Output format - 'json' or 'text' (default: 'text')

        Returns:
            List of containers in requested format

        Example:
            proxmox_list_containers()
            proxmox_list_containers(response_format="text")
        """
        try:
            # Validate and convert response_format string to enum
            input_data = ProxmoxListContainersInput(
                response_format=ResponseFormat(response_format.lower())
            )

            return proxmox_service.list_containers(
                response_format=input_data.response_format.value
            )

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp.tool(name="proxmox_container_status")
    async def proxmox_container_status(
        ctid: Annotated[int, "Container ID to check status for"] = 100,
        response_format: Annotated[str, "Output format: 'json' or 'text'"] = "text",
    ) -> str:
        """Get the current status of a specific Proxmox LXC container.

        This tool checks whether a container is running, stopped, or in another state.

        Args:
            ctid: Container ID to check
            response_format: Output format - 'json' or 'text' (default: 'text')

        Returns:
            Container status in requested format

        Example:
            proxmox_container_status(ctid=100)
            proxmox_container_status(ctid=101, response_format="text")
        """
        try:
            # Validate and convert response_format string to enum
            input_data = ProxmoxContainerStatusInput(
                ctid=ctid, response_format=ResponseFormat(response_format.lower())
            )

            return proxmox_service.get_container_status(
                ctid=input_data.ctid, response_format=input_data.response_format.value
            )

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp.tool(name="proxmox_start_container")
    async def proxmox_start_container(
        ctid: Annotated[int, "Container ID to start"] = 100,
    ) -> str:
        """Start a stopped Proxmox LXC container.

        This tool starts a container if it's currently stopped. If the container
        is already running, the operation has no effect (idempotent).

        Args:
            ctid: Container ID to start

        Returns:
            JSON result with success status and message

        Example:
            proxmox_start_container(ctid=100)
        """
        try:
            input_data = ProxmoxContainerActionInput(ctid=ctid)

            return proxmox_service.start_container(ctid=input_data.ctid)

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp.tool(name="proxmox_stop_container")
    async def proxmox_stop_container(
        ctid: Annotated[int, "Container ID to stop"] = 100,
    ) -> str:
        """Stop a running Proxmox LXC container.

        This tool gracefully stops a container if it's currently running. If the
        container is already stopped, the operation has no effect (idempotent).

        Args:
            ctid: Container ID to stop

        Returns:
            JSON result with success status and message

        Example:
            proxmox_stop_container(ctid=100)
        """
        try:
            input_data = ProxmoxContainerActionInput(ctid=ctid)

            return proxmox_service.stop_container(ctid=input_data.ctid)

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    _log.info("Registered 5 Proxmox container management tools")


def register_proxmox_file_tools(mcp: FastMCP, container: ServiceContainer) -> None:
    """
    Register Proxmox file transfer tools with the MCP server.

    These tools are disabled when ImageKit plugin is enabled to provide
    a unified file transfer interface.

    Args:
        mcp: FastMCP server instance
        container: Service container with core services
    """
    # Get Proxmox service from plugin services
    proxmox_service_obj = container.plugin_services.get("proxmox")
    if not proxmox_service_obj or not isinstance(proxmox_service_obj, ProxmoxService):
        _log.error("Proxmox service not found in plugin services")
        return

    proxmox_service: ProxmoxService = proxmox_service_obj

    @mcp.tool(name="proxmox_download_file_from_container")
    async def proxmox_download_file_from_container(
        ctid: Annotated[int, "Container ID to download file from"] = 100,
        container_path: Annotated[
            str, "Path to file inside the container"
        ] = "/etc/hostname",
        local_path: Annotated[str, "Local path where file will be saved"] = "./file",
        overwrite: Annotated[
            bool, "Whether to overwrite local file if it exists (default: False)"
        ] = False,
    ) -> str:
        """Download a file from a Proxmox LXC container to local machine.

        This tool downloads files from inside containers to your local machine using
        'pct pull' and SFTP.

        Use cases:
        - Download configuration files for backup or editing
        - Retrieve log files for analysis
        - Export data from containers
        - Backup important files before making changes

        Args:
            ctid: Container ID
            container_path: Path to file inside container (e.g., '/etc/nginx/nginx.conf')
            local_path: Local path where file will be saved (e.g., './nginx.conf')
            overwrite: Whether to overwrite local file if exists (default: False)

        Returns:
            JSON result with success status and details

        Example:
            proxmox_download_file_from_container(
                ctid=100,
                container_path="/etc/nginx/nginx.conf",
                local_path="./nginx.conf"
            )
        """
        try:
            input_data = ProxmoxDownloadFileInput(
                ctid=ctid,
                container_path=container_path,
                local_path=local_path,
                overwrite=overwrite,
            )

            return proxmox_service.download_file_from_container(
                ctid=input_data.ctid,
                container_path=input_data.container_path,
                local_path=input_data.local_path,
                overwrite=input_data.overwrite,
            )

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    @mcp.tool(name="proxmox_upload_file_to_container")
    async def proxmox_upload_file_to_container(
        ctid: Annotated[int, "Container ID to upload file to"] = 100,
        local_path: Annotated[str, "Local path to file to upload"] = "./file",
        container_path: Annotated[
            str, "Destination path inside container"
        ] = "/tmp/file",  # nosec B108  # Example path on remote container
        permissions: Annotated[
            int | None, "File permissions as octal (e.g., 644, 755)"
        ] = None,
        overwrite: Annotated[
            bool, "Whether to overwrite container file if it exists (default: False)"
        ] = False,
    ) -> str:
        """Upload a file from local machine to a Proxmox LXC container.

        This tool uploads files from your local machine to inside containers using
        SFTP and 'pct push'.

        Use cases:
        - Deploy configuration files to containers
        - Upload scripts for execution
        - Transfer data files to container applications
        - Update application code or assets

        Args:
            ctid: Container ID
            local_path: Local path to file to upload (e.g., './config.yaml')
            container_path: Destination path inside container (e.g., '/etc/app/config.yaml')
            permissions: File permissions as octal (e.g., 644, 755) (default: None, uses server's umask)
            overwrite: Whether to overwrite container file if exists (default: False)

        Returns:
            JSON result with success status and details

        Example:
            proxmox_upload_file_to_container(
                ctid=100,
                local_path="./nginx.conf",
                container_path="/etc/nginx/nginx.conf",
                overwrite=True
            )
        """
        try:
            input_data = ProxmoxUploadFileInput(
                ctid=ctid,
                local_path=local_path,
                container_path=container_path,
                permissions=permissions,
                overwrite=overwrite,
            )

            return proxmox_service.upload_file_to_container(
                ctid=input_data.ctid,
                local_path=input_data.local_path,
                container_path=input_data.container_path,
                permissions=input_data.permissions,
                overwrite=input_data.overwrite,
            )

        except ValueError as e:
            return container.output_formatter.format_error_result(
                f"Input validation error: {str(e)}"
            ).content
        except Exception as e:
            return container.output_formatter.format_error_result(
                f"Unexpected error: {str(e)}"
            ).content

    _log.info("Registered 2 Proxmox file transfer tools")
