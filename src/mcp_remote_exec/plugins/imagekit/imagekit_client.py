"""
ImageKit Client Wrapper for SSH MCP Remote Exec

Handles ImageKit SDK operations for file uploads/downloads.
"""

import logging
import os
from typing import Any

import requests
from imagekitio import ImageKit
from imagekitio.models.UploadFileRequestOptions import UploadFileRequestOptions
from imagekitio.models.ListAndSearchFileRequestOptions import (
    ListAndSearchFileRequestOptions,
)

from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig

_log = logging.getLogger(__name__)


class ImageKitClient:
    """Wrapper for ImageKit SDK operations"""

    def __init__(self, config: ImageKitConfig):
        """
        Initialize ImageKit client.

        Args:
            config: ImageKit configuration
        """
        self.config = config
        self._client = ImageKit(
            private_key=config.private_key,
            public_key=config.public_key,
            url_endpoint=config.url_endpoint,
        )

    def generate_upload_token(self, file_name: str) -> dict[str, Any]:
        """
        Generate authentication parameters for client-side upload.

        Args:
            file_name: Name for the uploaded file

        Returns:
            Dict with token, expire, signature
        """
        _log.debug(f"Generating upload token for {file_name}")

        auth_params = self._client.get_authentication_parameters()

        return {
            "token": auth_params["token"],
            "expire": auth_params["expire"],
            "signature": auth_params["signature"],
            "file_name": file_name,
            "public_key": self.config.public_key,
        }

    def build_upload_command(self, file_name: str) -> str:
        """
        Build curl command for client-side upload.

        Args:
            file_name: Name for the uploaded file

        Returns:
            Curl command string
        """
        auth = self.generate_upload_token(file_name)

        # Build curl command for client to execute
        # Client needs to replace LOCAL_FILE_PATH with their actual file path
        cmd = (
            f"curl -X POST 'https://upload.imagekit.io/api/v1/files/upload' \\\n"
            f"  -F 'file=@LOCAL_FILE_PATH' \\\n"
            f"  -F 'fileName={auth['file_name']}' \\\n"
            f"  -F 'useUniqueFileName=false' \\\n"
            f"  -F 'folder={self.config.folder}' \\\n"
            f"  -F 'publicKey={auth['public_key']}' \\\n"
            f"  -F 'signature={auth['signature']}' \\\n"
            f"  -F 'expire={auth['expire']}' \\\n"
            f"  -F 'token={auth['token']}'"
        )

        return cmd

    def upload_file(self, file_path: str, file_name: str) -> dict[str, Any]:
        """
        Upload file to ImageKit (server-side).

        Args:
            file_path: Local file path to upload
            file_name: Name for the uploaded file

        Returns:
            Dict with file_id, url, name
        """
        _log.info(f"Uploading {file_path} to ImageKit as {file_name}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as file:
            options = UploadFileRequestOptions(
                folder=self.config.folder,
                use_unique_file_name=False,
            )
            result = self._client.upload_file(
                file=file, file_name=file_name, options=options
            )

        _log.debug(f"Upload complete: {result.file_id}")

        return {
            "file_id": result.file_id,
            "url": result.url,
            "name": result.name,
        }

    def get_file_url(self, file_id: str) -> str:
        """
        Get direct URL for a file.

        Args:
            file_id: ImageKit file ID

        Returns:
            Direct URL to file
        """
        details = self._client.get_file_details(file_id)
        return str(details.url)

    def download_file(self, file_id: str, destination_path: str) -> int:
        """
        Download file from ImageKit to local path.

        Args:
            file_id: ImageKit file ID
            destination_path: Where to save the file

        Returns:
            Number of bytes downloaded
        """
        _log.info(f"Downloading {file_id} to {destination_path}")

        # Get file URL
        file_url = self.get_file_url(file_id)

        # Download file with timeout (30s connect, 300s read for large files)
        response = requests.get(file_url, timeout=(30, 300))
        response.raise_for_status()

        # Ensure directory exists
        os.makedirs(os.path.dirname(destination_path) or ".", exist_ok=True)

        # Write to file
        with open(destination_path, "wb") as f:
            f.write(response.content)

        bytes_written = len(response.content)
        _log.debug(f"Downloaded {bytes_written} bytes")

        return bytes_written

    def delete_file(self, file_id: str) -> bool:
        """
        Delete file from ImageKit.

        Args:
            file_id: ImageKit file ID

        Returns:
            True if deleted successfully
        """
        _log.info(f"Deleting file {file_id} from ImageKit")

        try:
            self._client.delete_file(file_id)
            _log.debug(f"Deleted file {file_id}")
            return True
        except Exception as e:
            _log.error(f"Failed to delete file {file_id}: {e}")
            return False

    def get_file_by_name(self, file_name: str) -> dict[str, Any] | None:
        """
        Search for file by name using ImageKit search API.

        Args:
            file_name: File name to search

        Returns:
            File info dict if found, None otherwise
        """
        try:
            _log.info(f"Searching for file: {file_name}")

            # Use search_query for efficient search (doesn't list all files)
            options = ListAndSearchFileRequestOptions(
                search_query=f'name="{file_name}"',
                path=self.config.folder,
                limit=10,  # Limit results for efficiency
            )

            result = self._client.list_files(options)
            _log.info(f"Search result count: {len(result.list) if result else 0}")

            if result and len(result.list) > 0:
                # Find exact match (case-insensitive)
                for file_info in result.list:
                    _log.info(f"Found file: {file_info.name}")
                    if file_info.name.lower() == file_name.lower():
                        _log.info(f"Exact match found: {file_info.name}")
                        return {
                            "file_id": file_info.file_id,
                            "url": file_info.url,
                            "name": file_info.name,
                        }

                # If no exact match but we have results, return first one
                _log.warning(
                    f"No exact match, using first result: {result.list[0].name}"
                )
                return {
                    "file_id": result.list[0].file_id,
                    "url": result.list[0].url,
                    "name": result.list[0].name,
                }

        except Exception as e:
            _log.error(f"Error searching for file {file_name}: {e}", exc_info=True)

        _log.warning(f"File {file_name} not found")
        return None
