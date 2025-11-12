"""
File Transfer Service for SSH MCP Remote Exec

Provides business logic for file upload/download operations with validation.
"""

import logging
from datetime import datetime

from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.sftp_manager import SFTPManager, FileTransferResult
from mcp_remote_exec.services.output_formatter import OutputFormatter

_log = logging.getLogger(__name__)


class FileTransferService:
    """Provides business logic for file transfer operations"""

    def __init__(self, sftp_manager: SFTPManager, config: SSHConfig):
        """Initialize file transfer service with dependencies"""
        self.sftp_manager = sftp_manager
        self.config = config
        self.output_formatter = OutputFormatter(config)

    def download_file(
        self, remote_path: str, local_path: str, overwrite: bool = False
    ) -> str:
        """Download file from remote server"""

        try:
            _log.debug(f"Download requested: {remote_path} -> {local_path}")
            # Perform download (validation and directory creation delegated to SFTPManager)
            transfer_result = self.sftp_manager.download_file(
                remote_path, local_path, overwrite
            )

            if transfer_result.success:
                formatted_result = self.output_formatter.format_file_transfer_result(
                    transfer_result
                )

                # Add transfer metadata
                metadata = self._add_transfer_metadata(transfer_result, "download")
                formatted_result.content += metadata

                return formatted_result.content
            else:
                _log.warning(f"Download failed: {transfer_result.message}")
                return self.output_formatter.format_error_result(
                    transfer_result.message
                ).content

        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            context = f"Remote: {remote_path}, Local: {local_path}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        permissions: int | None = None,
        overwrite: bool = False,
    ) -> str:
        """Upload file to remote server"""

        try:
            _log.debug(f"Upload requested: {local_path} -> {remote_path}")
            # Perform upload (validation delegated to SFTPManager)
            transfer_result = self.sftp_manager.upload_file(
                local_path, remote_path, permissions, overwrite
            )

            if transfer_result.success:
                formatted_result = self.output_formatter.format_file_transfer_result(
                    transfer_result
                )

                # Add transfer metadata
                metadata = self._add_transfer_metadata(
                    transfer_result, "upload", permissions
                )
                formatted_result.content += metadata

                return formatted_result.content
            else:
                _log.warning(f"Upload failed: {transfer_result.message}")
                return self.output_formatter.format_error_result(
                    transfer_result.message
                ).content

        except Exception as e:
            error_msg = f"Upload failed: {str(e)}"
            context = f"Local: {local_path}, Remote: {remote_path}"
            _log.error(f"{error_msg} - {context}")
            return self.output_formatter.format_error_result(error_msg, context).content

    def _add_transfer_metadata(
        self,
        result: FileTransferResult,
        operation: str,
        permissions: int | None = None,
    ) -> str:
        """Add metadata to file transfer result"""

        host_config = self.config.get_host()
        metadata = [
            "\n\n=== TRANSFER METADATA ===",
            f"Host: {host_config.name}",
            f"Operation: {operation}",
            f"Timestamp: {datetime.now().isoformat()}",
        ]

        if result.bytes_transferred > 0:
            metadata.append(f"Bytes transferred: {result.bytes_transferred}")

        if result.transfer_speed > 0:
            metadata.append(f"Transfer speed: {result.transfer_speed:.0f} bytes/s")

        if permissions:
            metadata.append(f"Permissions set: {permissions}")

        return "\n".join(metadata)
