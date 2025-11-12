"""
SFTP Manager for SSH MCP Remote Exec

Handles file upload/download operations via SFTP with security validation
and proper error handling.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from paramiko import SFTPClient, SSHException

from mcp_remote_exec.data_access.exceptions import SFTPError, FileValidationError
from mcp_remote_exec.data_access.path_validator import PathValidator

if TYPE_CHECKING:
    from mcp_remote_exec.data_access.ssh_connection_manager import SSHConnectionManager

_log = logging.getLogger(__name__)


@dataclass
class FileTransferResult:
    """Result of file transfer operation"""

    success: bool  # Whether the file transfer completed successfully
    message: str  # Human-readable result or error message
    bytes_transferred: int = 0  # Total number of bytes transferred
    transfer_speed: float = 0.0  # Transfer speed in bytes per second
    local_path: str | None = (
        None  # Local file system path (source for upload, destination for download)
    )
    remote_path: str | None = (
        None  # Remote server path (destination for upload, source for download)
    )
    operation: str = ""  # Type of operation: "upload" or "download"


class SFTPManager:
    """Manages SFTP operations for file transfers"""

    def __init__(self, connection_manager: "SSHConnectionManager") -> None:
        """Initialize SFTP manager with connection manager"""
        self.connection_manager = connection_manager
        self._sftp_client: SFTPClient | None = None

    def _get_sftp_client(self) -> SFTPClient:
        """Get SFTP client, creating if needed"""
        if self._sftp_client is None:
            try:
                ssh_client = self.connection_manager.get_connection()
                self._sftp_client = ssh_client.open_sftp()
                _log.info("Created SFTP client")
            except SSHException as e:
                raise SFTPError(
                    f"Failed to create SFTP client: {str(e)}",
                    operation="connect",
                )

        return self._sftp_client

    def _validate_file_path(
        self,
        file_path: str,
        remote_operation: bool = True,
        check_existence: bool = True,
    ) -> None:
        """
        Validate file path for security (prevent directory traversal).

        Delegates to PathValidator for centralized validation logic.

        Args:
            file_path: Path to validate
            remote_operation: True for remote paths, False for local paths
            check_existence: Whether to check if local file exists
        """
        path_type = "remote" if remote_operation else "local"
        PathValidator.validate_path(
            file_path,
            check_traversal=True,
            check_exists=(check_existence and not remote_operation),
            path_type=path_type,
        )

    def _validate_file_size(self, file_path: str) -> int:
        """Validate file size against limits for upload operations.

        Note: For downloads, file size is validated in download_file() after
        retrieving remote file stats via SFTP. This method is only used for uploads.
        """
        max_size = self.connection_manager.config.security.max_file_size

        # Local file size check for upload
        if not os.path.exists(file_path):
            raise FileValidationError(
                f"Local file does not exist: {file_path}",
                file_path,
                "file_not_found",
            )

        file_size = os.path.getsize(file_path)

        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            limit_mb = max_size / (1024 * 1024)
            raise FileValidationError(
                f"File too large ({size_mb:.1f}MB). Maximum allowed size is {limit_mb:.1f}MB.",
                file_path,
                "file_too_large",
            )

        return file_size

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        permissions: int | None = None,
        overwrite: bool = False,
    ) -> FileTransferResult:
        """Upload file to remote host via SFTP

        Args:
            local_path: Path to local file to upload
            remote_path: Destination path on remote server
            permissions: File permissions in octal notation as decimal integer.
                        User provides: 644 (representing octal notation)
                        Converts to: 0o644 (420 in decimal) = rw-r--r--
                        Common values: 644 (rw-r--r--), 755 (rwxr-xr-x),
                                     600 (rw-------), 700 (rwx------)
            overwrite: Whether to overwrite existing remote files

        Returns:
            FileTransferResult with success status and metadata
        """

        # Validate inputs
        try:
            self._validate_file_path(
                local_path, remote_operation=False, check_existence=True
            )
            self._validate_file_path(remote_path, remote_operation=True)
            file_size = self._validate_file_size(local_path)
        except FileValidationError as e:
            return FileTransferResult(
                success=False,
                message=str(e),
                local_path=local_path,
                remote_path=remote_path,
                operation="upload",
            )

        _log.info(f"Starting upload: {local_path} -> {remote_path}")

        try:
            sftp_client = self._get_sftp_client()

            # Check if remote file already exists
            try:
                sftp_client.stat(remote_path)
                if not overwrite:
                    error_msg = f"Remote file already exists: {remote_path}. Use overwrite=true to force overwrite."
                    return FileTransferResult(
                        success=False,
                        message=error_msg,
                        local_path=local_path,
                        remote_path=remote_path,
                        operation="upload",
                    )
                else:
                    # Remove existing file if overwrite is True
                    try:
                        sftp_client.remove(remote_path)
                        _log.info(f"Removed existing file: {remote_path}")
                    except Exception as e:
                        _log.warning(
                            f"Failed to remove existing file {remote_path}: {str(e)}"
                        )
            except IOError:
                # File doesn't exist, which is good
                pass

            # Transfer the file
            start_time = time.time()

            try:
                sftp_client.put(local_path, remote_path)
            except Exception as e:
                raise SFTPError(
                    f"File transfer failed: {str(e)}",
                    operation="upload",
                    path=remote_path,
                )

            # Set file permissions if specified
            if permissions is not None:
                try:
                    # Convert octal notation (as decimal int) to actual octal value
                    # Example: 644 -> int("644", 8) -> 0o644 (420 in decimal)
                    perm_str = str(permissions)

                    # Validate all digits are 0-7 (valid octal)
                    if not all(c in "01234567" for c in perm_str):
                        raise ValueError(
                            f"Invalid octal notation: {permissions}. Each digit must be 0-7. "
                            f"Common values: 644, 755, 600, 700"
                        )

                    octal_value = int(perm_str, 8)
                    sftp_client.chmod(remote_path, octal_value)
                    _log.info(
                        f"Set file permissions to {perm_str} ({oct(octal_value)}) on {remote_path}"
                    )
                except ValueError as e:
                    error_msg = f"Invalid permission value: {str(e)}"
                    _log.error(error_msg)
                    raise FileValidationError(
                        error_msg, remote_path, "invalid_permissions"
                    )
                except Exception as e:
                    _log.warning(
                        f"Failed to set permissions on {remote_path}: {str(e)}"
                    )

            transfer_time = time.time() - start_time
            speed = file_size / transfer_time if transfer_time > 0 else 0

            _log.info(
                f"Upload completed: {file_size} bytes in {transfer_time:.2f}s ({speed:.0f} bytes/s)"
            )

            return FileTransferResult(
                success=True,
                message=f"Successfully uploaded {local_path} to {remote_path}",
                bytes_transferred=file_size,
                transfer_speed=speed,
                local_path=local_path,
                remote_path=remote_path,
                operation="upload",
            )

        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            _log.error(error_msg)
            return FileTransferResult(
                success=False,
                message=error_msg,
                local_path=local_path,
                remote_path=remote_path,
                operation="upload",
            )

    def download_file(
        self, remote_path: str, local_path: str, overwrite: bool = False
    ) -> FileTransferResult:
        """Download file from remote host via SFTP"""

        # Validate inputs
        try:
            # Don't check for local file existence on download - we'll create/overwrite it
            self._validate_file_path(
                local_path, remote_operation=False, check_existence=False
            )
            self._validate_file_path(remote_path, remote_operation=True)
        except FileValidationError as e:
            return FileTransferResult(
                success=False,
                message=str(e),
                local_path=local_path,
                remote_path=remote_path,
                operation="download",
            )

        _log.info(f"Starting download: {remote_path} -> {local_path}")

        try:
            sftp_client = self._get_sftp_client()

            # Check if local file already exists and handle based on overwrite flag
            if os.path.exists(local_path):
                if not overwrite:
                    error_msg = f"Local file already exists: {local_path}. Use overwrite=true to force overwrite."
                    return FileTransferResult(
                        success=False,
                        message=error_msg,
                        local_path=local_path,
                        remote_path=remote_path,
                        operation="download",
                    )
                else:
                    # Remove existing local file if overwrite is True
                    try:
                        os.remove(local_path)
                        _log.info(f"Removed existing local file: {local_path}")
                    except Exception as e:
                        _log.warning(
                            f"Failed to remove existing local file {local_path}: {str(e)}"
                        )

            # Check remote file exists and get size
            try:
                remote_stat = sftp_client.stat(remote_path)
                file_size = remote_stat.st_size or 0
            except IOError:
                error_msg = (
                    f"Remote file does not exist or is not accessible: {remote_path}"
                )
                return FileTransferResult(
                    success=False,
                    message=error_msg,
                    local_path=local_path,
                    remote_path=remote_path,
                    operation="download",
                )

            # Validate file size
            try:
                max_size = self.connection_manager.config.security.max_file_size
                if file_size > max_size:
                    size_mb = file_size / (1024 * 1024)
                    limit_mb = max_size / (1024 * 1024)
                    error_msg = f"Remote file too large ({size_mb:.1f}MB). Maximum allowed size is {limit_mb:.1f}MB."
                    return FileTransferResult(
                        success=False,
                        message=error_msg,
                        local_path=local_path,
                        remote_path=remote_path,
                        operation="download",
                    )
            except FileValidationError as e:
                return FileTransferResult(
                    success=False,
                    message=str(e),
                    local_path=local_path,
                    remote_path=remote_path,
                    operation="download",
                )

            # Create local directory if needed
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)

            # Transfer the file
            start_time = time.time()

            try:
                sftp_client.get(remote_path, local_path)
            except Exception as e:
                raise SFTPError(
                    f"File transfer failed: {str(e)}",
                    operation="download",
                    path=remote_path,
                )

            transfer_time = time.time() - start_time
            speed = file_size / transfer_time if transfer_time > 0 else 0

            _log.info(
                f"Download completed: {file_size} bytes in {transfer_time:.2f}s ({speed:.0f} bytes/s)"
            )

            return FileTransferResult(
                success=True,
                message=f"Successfully downloaded {remote_path} to {local_path}",
                bytes_transferred=file_size,
                transfer_speed=speed,
                local_path=local_path,
                remote_path=remote_path,
                operation="download",
            )

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            _log.error(error_msg)
            return FileTransferResult(
                success=False,
                message=error_msg,
                local_path=local_path,
                remote_path=remote_path,
                operation="download",
            )

    def close_sftp_connection(self) -> None:
        """Close SFTP connection"""
        if self._sftp_client is None:
            return
        try:
            _log.info("Closing SFTP connection")
            self._sftp_client.close()
        except Exception as e:
            _log.warning(f"Error closing SFTP connection: {str(e)}")
        finally:
            self._sftp_client = None

    def __del__(self) -> None:
        """Cleanup on object destruction"""
        self.close_sftp_connection()

    def __enter__(self) -> "SFTPManager":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit with cleanup"""
        self.close_sftp_connection()
