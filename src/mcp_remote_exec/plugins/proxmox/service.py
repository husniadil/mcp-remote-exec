"""
Proxmox Service for SSH MCP Remote Exec

Business logic for Proxmox container operations.
"""

import json
import logging
import os
import uuid
from typing import Any

from mcp_remote_exec.constants import MSG_CONTAINER_NOT_FOUND, TEMP_FILE_PREFIX
from mcp_remote_exec.data_access.path_validator import PathValidator
from mcp_remote_exec.services.command_service import CommandService
from mcp_remote_exec.services.file_transfer_service import FileTransferService

_log = logging.getLogger(__name__)


class ProxmoxService:
    """Service for Proxmox container management operations"""

    def __init__(
        self,
        command_service: CommandService,
        file_service: FileTransferService,
    ):
        """Initialize Proxmox service with dependencies"""
        self.command_service = command_service
        self.file_service = file_service

    def exec_in_container(
        self, ctid: int, command: str, timeout: int, response_format: str
    ) -> str:
        """
        Execute a command inside a Proxmox LXC container.

        Args:
            ctid: Container ID
            command: Command to execute
            timeout: Command timeout in seconds
            response_format: Output format ('text' or 'json')

        Returns:
            Formatted command output
        """
        # Escape single quotes in command
        escaped_command = command.replace("'", "'\\''")
        pct_command = f"pct exec {ctid} -- bash -c '{escaped_command}'"

        _log.debug(f"Executing in container {ctid}: {command[:100]}")

        try:
            return self.command_service.execute_command(
                pct_command, timeout, response_format
            )
        except Exception as e:
            error_msg = str(e)
            if (
                "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                return self._format_error(
                    f"Container {ctid} not found or not accessible",
                    MSG_CONTAINER_NOT_FOUND,
                    response_format,
                )
            raise

    def list_containers(self, response_format: str) -> str:
        """
        List all LXC containers on the Proxmox host.

        Args:
            response_format: Output format ('text' or 'json')

        Returns:
            List of containers in requested format
        """
        _log.debug("Listing Proxmox containers")

        result = self.command_service.execute_command("pct list", 30, "text")

        # Extract stdout from result (strip metadata and formatting)
        stdout = self._extract_stdout(result)

        # Parse output
        containers = self._parse_pct_list_output(stdout)

        if response_format.lower() == "json":
            return json.dumps(containers, indent=2)
        else:
            # Text format
            if not containers:
                return "No containers found"

            lines = ["CTID | Status  | Name", "-" * 50]
            for ct in containers:
                lines.append(f"{ct['ctid']:4d} | {ct['status']:7s} | {ct['name']}")

            return "\n".join(lines)

    def get_container_status(self, ctid: int, response_format: str) -> str:
        """
        Get the status of a specific container.

        Args:
            ctid: Container ID
            response_format: Output format ('text' or 'json')

        Returns:
            Container status in requested format
        """
        _log.debug(f"Getting status for container {ctid}")

        try:
            result = self.command_service.execute_command(
                f"pct status {ctid}", 30, "text"
            )

            # Extract stdout
            stdout = self._extract_stdout(result)

            # Parse status
            status_data = self._parse_pct_status_output(stdout)

            if response_format.lower() == "json":
                return json.dumps(status_data, indent=2)
            else:
                return f"Container {ctid} is {status_data['status']}"

        except Exception as e:
            error_msg = str(e)
            if (
                "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                return self._format_error(
                    f"Container {ctid} not found",
                    MSG_CONTAINER_NOT_FOUND,
                    response_format,
                )
            raise

    def start_container(self, ctid: int) -> str:
        """
        Start a Proxmox LXC container.

        Args:
            ctid: Container ID

        Returns:
            JSON result with success status
        """
        _log.info(f"Starting container {ctid}")

        try:
            self.command_service.execute_command(f"pct start {ctid}", 30, "text")
            return json.dumps(
                {
                    "success": True,
                    "message": f"Container {ctid} started successfully",
                    "ctid": ctid,
                },
                indent=2,
            )
        except Exception as e:
            error_msg = str(e)
            if (
                "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Container {ctid} not found",
                        "suggestion": MSG_CONTAINER_NOT_FOUND,
                    },
                    indent=2,
                )
            return json.dumps(
                {"success": False, "error": f"Failed to start container: {error_msg}"},
                indent=2,
            )

    def stop_container(self, ctid: int) -> str:
        """
        Stop a Proxmox LXC container.

        Args:
            ctid: Container ID

        Returns:
            JSON result with success status
        """
        _log.info(f"Stopping container {ctid}")

        try:
            self.command_service.execute_command(f"pct stop {ctid}", 30, "text")
            return json.dumps(
                {
                    "success": True,
                    "message": f"Container {ctid} stopped successfully",
                    "ctid": ctid,
                },
                indent=2,
            )
        except Exception as e:
            error_msg = str(e)
            if (
                "does not exist" in error_msg.lower()
                or "not found" in error_msg.lower()
            ):
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Container {ctid} not found",
                        "suggestion": MSG_CONTAINER_NOT_FOUND,
                    },
                    indent=2,
                )
            return json.dumps(
                {"success": False, "error": f"Failed to stop container: {error_msg}"},
                indent=2,
            )

    def download_file_from_container(
        self, ctid: int, container_path: str, local_path: str, overwrite: bool
    ) -> str:
        """
        Download a file from a container to local machine.

        Uses pct pull + SFTP download + cleanup.

        Args:
            ctid: Container ID
            container_path: Path inside container
            local_path: Local destination path
            overwrite: Whether to overwrite local file

        Returns:
            JSON result with transfer details
        """
        _log.info(f"Downloading {container_path} from container {ctid}")

        # Validate paths for directory traversal
        is_valid, error = PathValidator.check_paths_for_traversal(
            container_path, local_path
        )
        if not is_valid:
            return json.dumps(
                {
                    "success": False,
                    "error": error,
                },
                indent=2,
            )

        # Check if local file exists
        if os.path.exists(local_path) and not overwrite:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Local file already exists: {local_path}",
                    "suggestion": "Set overwrite=true to replace existing file",
                },
                indent=2,
            )

        # Generate temp path on host
        temp_path = f"{TEMP_FILE_PREFIX}-{uuid.uuid4().hex}"

        try:
            # Pull file from container to host temp location
            pull_command = f"pct pull {ctid} {container_path} {temp_path}"
            pull_result = self.command_service.execute_command(pull_command, 30, "text")

            # Check if pull succeeded
            if "[ERROR]" in pull_result or "failed" in pull_result.lower():
                self._cleanup_temp_file(temp_path)
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Failed to pull file from container {ctid}",
                        "suggestion": "Check if container exists, is running, and file path is correct",
                    },
                    indent=2,
                )

            # Download from host to local
            download_result = self.file_service.download_file(
                temp_path, local_path, overwrite
            )

            # Cleanup temp file
            self._cleanup_temp_file(temp_path)

            # Check download result
            if "[ERROR]" in download_result:
                return download_result

            # Get file size
            file_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0

            return json.dumps(
                {
                    "success": True,
                    "message": f"File downloaded successfully from container {ctid}",
                    "ctid": ctid,
                    "container_path": container_path,
                    "local_path": local_path,
                    "bytes_transferred": file_size,
                },
                indent=2,
            )

        except Exception as e:
            self._cleanup_temp_file(temp_path)
            return json.dumps(
                {"success": False, "error": str(e)},
                indent=2,
            )

    def upload_file_to_container(
        self,
        ctid: int,
        local_path: str,
        container_path: str,
        permissions: int | None,
        overwrite: bool,
    ) -> str:
        """
        Upload a file from local machine to a container.

        Uses SFTP upload + pct push + chmod + cleanup.

        Args:
            ctid: Container ID
            local_path: Local file path
            container_path: Destination path inside container
            permissions: File permissions (octal)
            overwrite: Whether to overwrite container file

        Returns:
            JSON result with transfer details
        """
        _log.info(f"Uploading {local_path} to container {ctid}")

        # Validate paths for directory traversal
        is_valid, error = PathValidator.check_paths_for_traversal(
            container_path, local_path
        )
        if not is_valid:
            return json.dumps(
                {
                    "success": False,
                    "error": error,
                },
                indent=2,
            )

        # Check if local file exists
        if not os.path.exists(local_path):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Local file not found: {local_path}",
                },
                indent=2,
            )

        # Check if container file exists (unless overwrite is true)
        if not overwrite:
            check_command = f"pct exec {ctid} -- test -f {container_path}"
            check_result = self.command_service.execute_command(
                check_command, 30, "text"
            )
            # test command succeeds (exit 0) if file exists
            if "EXIT CODE: 0" in check_result:
                return json.dumps(
                    {
                        "success": False,
                        "error": f"File already exists in container: {container_path}",
                        "suggestion": "Set overwrite=true to replace existing file",
                    },
                    indent=2,
                )

        # Generate temp path on host
        temp_path = f"{TEMP_FILE_PREFIX}-{uuid.uuid4().hex}"

        try:
            # Upload from local to host temp location
            upload_result = self.file_service.upload_file(
                local_path, temp_path, None, True
            )

            if "[ERROR]" in upload_result:
                self._cleanup_temp_file(temp_path)
                return upload_result

            # Push file from host to container
            push_command = f"pct push {ctid} {temp_path} {container_path}"
            push_result = self.command_service.execute_command(push_command, 30, "text")

            if "[ERROR]" in push_result or "failed" in push_result.lower():
                self._cleanup_temp_file(temp_path)
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Failed to push file to container {ctid}",
                        "suggestion": "Check if container exists, is running, and destination path is valid",
                    },
                    indent=2,
                )

            # Set permissions if specified
            if permissions is not None:
                chmod_command = (
                    f"pct exec {ctid} -- chmod {permissions} {container_path}"
                )
                self.command_service.execute_command(chmod_command, 30, "text")

            # Cleanup temp file
            self._cleanup_temp_file(temp_path)

            # Get file size
            file_size = os.path.getsize(local_path)

            return json.dumps(
                {
                    "success": True,
                    "message": f"File uploaded successfully to container {ctid}",
                    "ctid": ctid,
                    "local_path": local_path,
                    "container_path": container_path,
                    "permissions": str(permissions) if permissions else "default",
                    "bytes_transferred": file_size,
                },
                indent=2,
            )

        except Exception as e:
            self._cleanup_temp_file(temp_path)
            return json.dumps(
                {"success": False, "error": str(e)},
                indent=2,
            )

    def _cleanup_temp_file(self, temp_path: str) -> None:
        """Remove temporary file on Proxmox host"""
        try:
            self.command_service.execute_command(f"rm -f {temp_path}", 5, "text")
        except Exception:  # nosec B110
            # Ignore cleanup errors - best effort temp file removal
            pass

    def _extract_stdout(self, result: str) -> str:
        """
        Extract stdout from command service result.

        Command service returns formatted output like:
        === STDOUT ===
        actual command output

        === EXIT CODE: 0 ===

        === EXECUTION METADATA ===
        ...

        Args:
            result: Formatted command result

        Returns:
            Clean stdout without formatting headers
        """
        lines = result.split("\n")
        stdout_lines = []
        in_stdout = False

        for line in lines:
            if "=== STDOUT ===" in line:
                in_stdout = True
                continue
            if line.startswith("==="):
                # Hit another section (STDERR, EXIT CODE, METADATA)
                in_stdout = False
                continue
            if in_stdout:
                stdout_lines.append(line)

        return "\n".join(stdout_lines)

    def _parse_pct_list_output(self, output: str) -> list[dict[str, Any]]:
        """Parse 'pct list' command output into structured data"""
        lines = output.strip().split("\n")
        if len(lines) < 2:
            return []

        # First line is header
        containers = []
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 3:
                containers.append(
                    {
                        "ctid": int(parts[0]),
                        "status": parts[1],
                        "name": " ".join(parts[2:]),  # Handle names with spaces
                    }
                )

        return containers

    def _parse_pct_status_output(self, output: str) -> dict[str, str]:
        """Parse 'pct status' command output"""
        output = output.strip().lower()
        if "running" in output:
            status = "running"
        elif "stopped" in output:
            status = "stopped"
        else:
            status = "unknown"

        return {"status": status}

    def _format_error(self, error: str, suggestion: str, response_format: str) -> str:
        """Format error message based on response format"""
        if response_format.lower() == "json":
            return json.dumps(
                {"success": False, "error": error, "suggestion": suggestion}, indent=2
            )
        else:
            return f"Error: {error}\n\nSuggestion: {suggestion}"
