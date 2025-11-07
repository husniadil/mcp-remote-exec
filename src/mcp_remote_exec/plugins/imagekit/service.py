"""
ImageKit Service for SSH MCP Remote Exec

Business logic for ImageKit file transfer operations.
"""

import json
import logging
import os
import tempfile
from typing import Any

from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig
from mcp_remote_exec.plugins.imagekit.imagekit_client import ImageKitClient
from mcp_remote_exec.plugins.imagekit.transfer_manager import TransferManager
from mcp_remote_exec.plugins.imagekit.models import (
    TransferOperation,
    UploadRequestResult,
    DownloadRequestResult,
    TransferConfirmResult,
)
from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager
from mcp_remote_exec.data_access.sftp_manager import SFTPManager

_log = logging.getLogger(__name__)


class ImageKitService:
    """Service for ImageKit file transfer operations"""

    def __init__(
        self,
        config: ImageKitConfig,
        connection_manager: SSHConnectionManager,
        sftp_manager: SFTPManager,
    ):
        """
        Initialize ImageKit service.

        Args:
            config: ImageKit configuration
            connection_manager: SSH connection manager for server-side operations
            sftp_manager: SFTP manager for file transfers between MCP server and SSH host
        """
        self.config = config
        self.connection_manager = connection_manager
        self.sftp_manager = sftp_manager
        self.client = ImageKitClient(config)
        self.transfer_manager = TransferManager(timeout_seconds=config.transfer_timeout)

    def request_upload(
        self,
        remote_path: str,
        permissions: int | None = None,
        overwrite: bool = False,
        ctid: int | None = None,
    ) -> str:
        """
        Initiate upload from client to server.

        Args:
            remote_path: Destination path (on host if ctid=None, in container if ctid is set)
            permissions: Optional file permissions (octal)
            overwrite: Whether to overwrite existing file
            ctid: Optional Proxmox container ID - if set, file will be pushed to container

        Returns:
            JSON string with upload instructions
        """
        # Validate container access requires Proxmox plugin
        if ctid is not None:
            proxmox_enabled = os.getenv("ENABLE_PROXMOX", "false").lower() == "true"
            if not proxmox_enabled:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Container file transfers require Proxmox plugin to be enabled",
                        "suggestion": "Set ENABLE_PROXMOX=true in your .env file to use container features (ctid parameter)",
                    },
                    indent=2,
                )

        if ctid:
            _log.info(f"Upload request for {remote_path} in container {ctid}")
        else:
            _log.info(f"Upload request for {remote_path} on host")

        # Validate remote path
        if ".." in remote_path:
            return json.dumps(
                {
                    "success": False,
                    "error": "Path cannot contain '..' (path traversal not allowed)",
                },
                indent=2,
            )

        # Check if file exists (if not overwriting)
        if not overwrite:
            try:
                ssh = self.connection_manager.get_connection()
                if ctid:
                    # Check in container
                    check_cmd = f"pct exec {ctid} -- test -f {remote_path}"
                    stdin, stdout, stderr = ssh.exec_command(check_cmd)
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:  # File exists in container
                        return json.dumps(
                            {
                                "success": False,
                                "error": f"File already exists in container {ctid}: {remote_path}",
                                "suggestion": "Set overwrite=true to replace existing file",
                            },
                            indent=2,
                        )
                else:
                    # Check on host
                    stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path}")
                    exit_code = stdout.channel.recv_exit_status()
                    if exit_code == 0:  # File exists on host
                        return json.dumps(
                            {
                                "success": False,
                                "error": f"File already exists on host: {remote_path}",
                                "suggestion": "Set overwrite=true to replace existing file",
                            },
                            indent=2,
                        )
            except Exception as e:
                _log.warning(f"Could not check if file exists: {e}")

        # Create transfer state
        transfer = self.transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path=remote_path,
            permissions=permissions,
            overwrite=overwrite,
            ctid=ctid,
        )

        # Generate upload command
        file_name = f"mcp-upload-{transfer.transfer_id}"
        upload_command = self.client.build_upload_command(file_name)

        result = UploadRequestResult(
            transfer_id=transfer.transfer_id,
            upload_command=upload_command.replace(
                "LOCAL_FILE_PATH", "<YOUR_FILE_PATH>"
            ),
            expires_in=self.config.transfer_timeout,
        )

        # Cleanup expired transfers
        self.transfer_manager.cleanup_expired_transfers()

        return json.dumps(result.model_dump(), indent=2)

    def confirm_upload(self, transfer_id: str, file_id: str | None = None) -> str:
        """
        Complete upload after client uploads to ImageKit.

        Args:
            transfer_id: Transfer identifier
            file_id: Optional ImageKit file ID (bypasses search if provided)

        Returns:
            JSON string with transfer result
        """
        _log.info(f"Upload confirmation for {transfer_id}")

        # Get transfer state
        transfer = self.transfer_manager.get_transfer(transfer_id)
        if not transfer:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Transfer {transfer_id} not found or expired",
                },
                indent=2,
            )

        if transfer.operation != TransferOperation.UPLOAD.value:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Transfer {transfer_id} is not an upload operation",
                },
                indent=2,
            )

        try:
            # Get file info - either by ID or by searching
            file_info: dict[str, Any] | None
            if file_id:
                _log.info(f"Using provided file_id: {file_id}")
                # When file_id is provided, we only need the ID for download
                # The URL will be retrieved by the client via get_file_url()
                file_info = {
                    "file_id": file_id,
                    "name": f"mcp-upload-{transfer_id}",
                }
            else:
                # Find file on ImageKit by name
                file_name = f"mcp-upload-{transfer_id}"
                file_info = self.client.get_file_by_name(file_name)

            if not file_info:
                return json.dumps(
                    {
                        "success": False,
                        "error": "File not found on ImageKit. Make sure upload completed successfully.",
                    },
                    indent=2,
                )

            # Download from ImageKit to MCP server temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                local_temp_path = tmp_file.name

            bytes_transferred = self.client.download_file(
                file_info["file_id"], local_temp_path
            )

            ssh = self.connection_manager.get_connection()

            if transfer.ctid:
                # Upload to container workflow
                _log.info(
                    f"Uploading to container {transfer.ctid}: {transfer.remote_path}"
                )

                # Upload from MCP server to host temp location via SFTP
                # Path is on remote SSH server, not local system
                host_temp_path = f"/tmp/mcp-imagekit-{transfer_id}"  # nosec B108
                upload_result = self.sftp_manager.upload_file(
                    local_path=local_temp_path,
                    remote_path=host_temp_path,
                    permissions=None,
                    overwrite=True,
                )

                if not upload_result.success:
                    os.unlink(local_temp_path)
                    self.transfer_manager.complete_transfer(transfer_id)
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Failed to upload to host: {upload_result.message}",
                        },
                        indent=2,
                    )

                # Push file from host to container
                stdin, stdout, stderr = ssh.exec_command(
                    f"pct push {transfer.ctid} {host_temp_path} {transfer.remote_path}"
                )
                exit_code = stdout.channel.recv_exit_status()

                if exit_code != 0:
                    error_output = stderr.read().decode()
                    # Cleanup
                    os.unlink(local_temp_path)
                    ssh.exec_command(f"rm -f {host_temp_path}")
                    self.transfer_manager.complete_transfer(transfer_id)
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Failed to push to container {transfer.ctid}: {error_output}",
                            "suggestion": "Check if container exists and is running",
                        },
                        indent=2,
                    )

                # Set permissions in container if specified
                if transfer.permissions is not None:
                    perm_str = str(transfer.permissions)
                    ssh.exec_command(
                        f"pct exec {transfer.ctid} -- chmod {perm_str} {transfer.remote_path}"
                    )

                # Cleanup temp files
                os.unlink(local_temp_path)
                ssh.exec_command(f"rm -f {host_temp_path}")

                message = f"Successfully uploaded to container {transfer.ctid}: {transfer.remote_path}"
            else:
                # Upload to host workflow (original behavior)
                _log.info(f"Uploading to host: {transfer.remote_path}")

                # Upload from MCP server to host via SFTP
                upload_result = self.sftp_manager.upload_file(
                    local_path=local_temp_path,
                    remote_path=transfer.remote_path,
                    permissions=transfer.permissions,
                    overwrite=transfer.overwrite,
                )

                # Cleanup local temp file
                os.unlink(local_temp_path)

                if not upload_result.success:
                    self.transfer_manager.complete_transfer(transfer_id)
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Failed to upload to host: {upload_result.message}",
                        },
                        indent=2,
                    )

                message = f"Successfully uploaded to host: {transfer.remote_path}"

            # Delete from ImageKit
            self.client.delete_file(file_info["file_id"])

            # Complete transfer
            self.transfer_manager.complete_transfer(transfer_id)

            result = TransferConfirmResult(
                success=True,
                message=message,
                remote_path=transfer.remote_path,
                bytes_transferred=bytes_transferred,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            _log.error(f"Upload confirmation failed: {e}")
            return json.dumps(
                {
                    "success": False,
                    "error": f"Upload failed: {str(e)}",
                },
                indent=2,
            )

    def request_download(self, remote_path: str, ctid: int | None = None) -> str:
        """
        Initiate download from server to client.

        Args:
            remote_path: Source path (on host if ctid=None, in container if ctid is set)
            ctid: Optional Proxmox container ID for downloading from container

        Returns:
            JSON string with download instructions
        """
        # Validate container access requires Proxmox plugin
        if ctid is not None:
            proxmox_enabled = os.getenv("ENABLE_PROXMOX", "false").lower() == "true"
            if not proxmox_enabled:
                return json.dumps(
                    {
                        "success": False,
                        "error": "Container file transfers require Proxmox plugin to be enabled",
                        "suggestion": "Set ENABLE_PROXMOX=true in your .env file to use container features (ctid parameter)",
                    },
                    indent=2,
                )

        if ctid:
            _log.info(f"Download request for {remote_path} from container {ctid}")
        else:
            _log.info(f"Download request for {remote_path} from host")

        # Validate remote path
        if ".." in remote_path:
            return json.dumps(
                {
                    "success": False,
                    "error": "Path cannot contain '..' (path traversal not allowed)",
                },
                indent=2,
            )

        # Check if file exists (in container or on host)
        try:
            ssh = self.connection_manager.get_connection()
            if ctid:
                # Check file in container
                check_cmd = f"pct exec {ctid} -- test -f {remote_path}"
            else:
                # Check file on host
                check_cmd = f"test -f {remote_path}"

            stdin, stdout, stderr = ssh.exec_command(check_cmd)
            exit_code = stdout.channel.recv_exit_status()
            if exit_code != 0:  # File doesn't exist
                location = f"container {ctid}" if ctid else "host"
                return json.dumps(
                    {
                        "success": False,
                        "error": f"File not found in {location}: {remote_path}",
                    },
                    indent=2,
                )
        except Exception as e:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Could not check file: {str(e)}",
                },
                indent=2,
            )

        # Create transfer state
        transfer = self.transfer_manager.create_transfer(
            operation=TransferOperation.DOWNLOAD,
            remote_path=remote_path,
            ctid=ctid,
        )

        try:
            # If downloading from container, first pull to host temp
            host_temp_path = None
            if ctid:
                _log.info(f"Pulling file from container {ctid}: {remote_path}")
                # Path is on remote SSH server, not local system
                host_temp_path = f"/tmp/mcp-imagekit-download-{transfer.transfer_id}"  # nosec B108

                ssh = self.connection_manager.get_connection()
                pull_cmd = f"pct pull {ctid} {remote_path} {host_temp_path}"
                stdin, stdout, stderr = ssh.exec_command(pull_cmd)
                exit_code = stdout.channel.recv_exit_status()

                if exit_code != 0:
                    error_msg = stderr.read().decode().strip()
                    self.transfer_manager.complete_transfer(transfer.transfer_id)
                    return json.dumps(
                        {
                            "success": False,
                            "error": f"Failed to pull from container {ctid}: {error_msg}",
                        },
                        indent=2,
                    )

                # Use the host temp path for SFTP download
                download_path = host_temp_path
            else:
                # Download directly from host
                download_path = remote_path

            # Download from remote server to local temp file using SFTP
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp_file:
                local_temp_path = tmp_file.name

            # Use SFTP to download file from remote host to MCP server
            download_result = self.sftp_manager.download_file(
                remote_path=download_path, local_path=local_temp_path, overwrite=True
            )

            if not download_result.success:
                os.unlink(local_temp_path)
                # Clean up host temp file if we created one
                if host_temp_path:
                    ssh = self.connection_manager.get_connection()
                    ssh.exec_command(f"rm -f {host_temp_path}")
                self.transfer_manager.complete_transfer(transfer.transfer_id)
                return json.dumps(
                    {
                        "success": False,
                        "error": f"Failed to download from remote: {download_result.message}",
                    },
                    indent=2,
                )

            # Clean up host temp file if we created one
            if host_temp_path:
                ssh = self.connection_manager.get_connection()
                ssh.exec_command(f"rm -f {host_temp_path}")

            # Upload to ImageKit from MCP server
            file_name = f"mcp-download-{transfer.transfer_id}"
            file_info = self.client.upload_file(local_temp_path, file_name)

            # Clean up local temp file
            os.unlink(local_temp_path)

            # Update transfer with ImageKit file ID
            self.transfer_manager.update_transfer(
                transfer.transfer_id, file_info["file_id"]
            )

            # Generate download command
            download_url = file_info["url"]
            download_command = f"curl -o '<YOUR_FILE_PATH>' '{download_url}'"

            result = DownloadRequestResult(
                transfer_id=transfer.transfer_id,
                download_url=download_url,
                download_command=download_command,
                expires_in=self.config.transfer_timeout,
            )

            # Cleanup expired transfers
            self.transfer_manager.cleanup_expired_transfers()

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            _log.error(f"Download request failed: {e}")
            self.transfer_manager.complete_transfer(transfer.transfer_id)
            return json.dumps(
                {
                    "success": False,
                    "error": f"Download preparation failed: {str(e)}",
                },
                indent=2,
            )

    def confirm_download(self, transfer_id: str) -> str:
        """
        Complete download and cleanup ImageKit.

        Args:
            transfer_id: Transfer identifier

        Returns:
            JSON string with cleanup result
        """
        _log.info(f"Download confirmation for {transfer_id}")

        # Get transfer state
        transfer = self.transfer_manager.get_transfer(transfer_id)
        if not transfer:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Transfer {transfer_id} not found or already completed",
                },
                indent=2,
            )

        if transfer.operation != TransferOperation.DOWNLOAD.value:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Transfer {transfer_id} is not a download operation",
                },
                indent=2,
            )

        try:
            # Delete from ImageKit
            if transfer.imagekit_file_id:
                self.client.delete_file(transfer.imagekit_file_id)

            # Complete transfer
            self.transfer_manager.complete_transfer(transfer_id)

            result = TransferConfirmResult(
                success=True,
                message="Download completed and cleaned up",
                remote_path=transfer.remote_path,
            )

            return json.dumps(result.model_dump(), indent=2)

        except Exception as e:
            _log.error(f"Download confirmation failed: {e}")
            return json.dumps(
                {
                    "success": False,
                    "error": f"Cleanup failed: {str(e)}",
                },
                indent=2,
            )
