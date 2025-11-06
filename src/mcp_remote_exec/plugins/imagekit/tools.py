"""
MCP Tools for ImageKit Plugin

Registers ImageKit file transfer tools.
"""

import logging
from typing import Annotated

from fastmcp import FastMCP
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.imagekit.service import ImageKitService
from mcp_remote_exec.plugins.imagekit.models import (
    ImageKitRequestUploadInput,
    ImageKitConfirmUploadInput,
    ImageKitRequestDownloadInput,
    ImageKitConfirmDownloadInput,
)

_log = logging.getLogger(__name__)


def register_imagekit_tools(mcp: FastMCP, container: ServiceContainer) -> None:
    """
    Register all ImageKit plugin tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        container: Service container with core services
    """
    # Get ImageKit service from plugin services
    imagekit_service_obj = container.plugin_services.get("imagekit")
    if not imagekit_service_obj or not isinstance(
        imagekit_service_obj, ImageKitService
    ):
        _log.error("ImageKit service not found in plugin services")
        return

    imagekit_service: ImageKitService = imagekit_service_obj

    @mcp.tool(name="imagekit_request_upload")
    async def imagekit_request_upload(
        remote_path: Annotated[
            str,
            "Destination path - on host if ctid=None, in container if ctid is set (e.g., '/data/file.txt' or '/app/config.txt')",
        ],
        permissions: Annotated[
            int | None, "File permissions as octal (e.g., 644, 755)"
        ] = None,
        overwrite: Annotated[
            bool, "Whether to overwrite existing file (default: False)"
        ] = False,
        ctid: Annotated[
            int | None,
            "Optional: Proxmox container ID - if provided, file will be automatically pushed to this container",
        ] = None,
    ) -> str:
        """Initiate file upload from client to server via ImageKit.

        This is step 1 of the two-phase upload process:
        1. Call this tool to get upload instructions
        2. Execute the returned curl command to upload your file
        3. Call imagekit_confirm_upload to complete the transfer

        The server generates a short-lived upload token and returns a curl command
        that you can use to upload your file directly to ImageKit.

        When ctid is provided, the file will be automatically pushed to the specified
        Proxmox container after upload completes.

        Args:
            remote_path: Destination path (on host if ctid=None, in container if ctid is set)
            permissions: File permissions as octal (e.g., 644, 755)
            overwrite: Whether to overwrite existing file (default: False)
            ctid: Optional Proxmox container ID for automatic push to container

        Returns:
            JSON with transfer_id, upload_command, and expires_in

        Examples:
            # Upload to host
            imagekit_request_upload(remote_path="/tmp/file.txt", permissions=644)

            # Upload to container 100
            imagekit_request_upload(remote_path="/app/config.txt", permissions=644, ctid=100)
        """
        try:
            input_data = ImageKitRequestUploadInput(
                remote_path=remote_path,
                permissions=permissions,
                overwrite=overwrite,
                ctid=ctid,
            )

            return imagekit_service.request_upload(
                remote_path=input_data.remote_path,
                permissions=input_data.permissions,
                overwrite=input_data.overwrite,
                ctid=input_data.ctid,
            )

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"

    @mcp.tool(name="imagekit_confirm_upload")
    async def imagekit_confirm_upload(
        transfer_id: Annotated[str, "Transfer ID from imagekit_request_upload"],
        file_id: Annotated[
            str | None,
            "Optional: ImageKit fileId from upload response (recommended for reliability)",
        ] = None,
    ) -> str:
        """Complete file upload after client uploads to ImageKit.

        This is step 3 of the two-phase upload process. Call this after you've
        executed the curl command from imagekit_request_upload.

        The server will:
        1. Download the file from ImageKit
        2. Save it to the requested remote path
        3. Set permissions if specified
        4. Delete the file from ImageKit

        Args:
            transfer_id: Transfer ID from imagekit_request_upload
            file_id: Optional ImageKit fileId from the upload response.
                     If provided, bypasses file search (RECOMMENDED for reliability).
                     Get this from the "fileId" field in the curl upload response.

        Returns:
            JSON with success status and transfer details

        Examples:
            # Without file_id (searches by name - may be slow/unreliable)
            imagekit_confirm_upload(transfer_id="abc-123-def")

            # With file_id (RECOMMENDED - no search, immediate processing)
            imagekit_confirm_upload(
                transfer_id="abc-123-def",
                file_id="690b82f45c7cd75eb8328078"
            )
        """
        try:
            input_data = ImageKitConfirmUploadInput(
                transfer_id=transfer_id, file_id=file_id
            )

            return imagekit_service.confirm_upload(
                transfer_id=input_data.transfer_id, file_id=input_data.file_id
            )

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"

    @mcp.tool(name="imagekit_request_download")
    async def imagekit_request_download(
        remote_path: Annotated[
            str,
            "Source path - on host if ctid=None, in container if ctid is set (e.g., '/data/file.txt')",
        ],
        ctid: Annotated[
            int | None,
            "Optional: Proxmox container ID - if provided, file will be pulled from this container",
        ] = None,
    ) -> str:
        """Initiate file download from server to client via ImageKit.

        This is step 1 of the two-phase download process:
        1. Call this tool to prepare the download
        2. Execute the returned curl command to download your file
        3. Call imagekit_confirm_download to clean up

        The server will upload the file to ImageKit and return a download URL
        that you can use to download the file.

        When ctid is provided, the file will be automatically pulled from the specified
        Proxmox container before upload to ImageKit.

        Args:
            remote_path: Source path (on host if ctid=None, in container if ctid is set)
            ctid: Optional Proxmox container ID for downloading from container

        Returns:
            JSON with transfer_id, download_url, download_command, and expires_in

        Examples:
            # Download from host
            imagekit_request_download(remote_path="/data/app.conf")

            # Download from container 100
            imagekit_request_download(remote_path="/app/logs/app.log", ctid=100)
        """
        try:
            input_data = ImageKitRequestDownloadInput(
                remote_path=remote_path, ctid=ctid
            )

            return imagekit_service.request_download(
                remote_path=input_data.remote_path, ctid=input_data.ctid
            )

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"

    @mcp.tool(name="imagekit_confirm_download")
    async def imagekit_confirm_download(
        transfer_id: Annotated[str, "Transfer ID from imagekit_request_download"],
    ) -> str:
        """Complete file download and clean up ImageKit.

        This is step 3 of the two-phase download process. Call this after you've
        downloaded the file using the URL from imagekit_request_download.

        The server will delete the file from ImageKit to complete the cleanup.

        Args:
            transfer_id: Transfer ID from imagekit_request_download

        Returns:
            JSON with success status

        Example:
            imagekit_confirm_download(transfer_id="abc-123-def")
        """
        try:
            input_data = ImageKitConfirmDownloadInput(transfer_id=transfer_id)

            return imagekit_service.confirm_download(transfer_id=input_data.transfer_id)

        except ValueError as e:
            return f"[ERROR] Input validation error: {str(e)}"
        except Exception as e:
            return f"[ERROR] Unexpected error: {str(e)}"

    _log.info("Registered 4 ImageKit file transfer tools")
