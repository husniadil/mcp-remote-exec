"""
ImageKit Configuration for SSH MCP Remote Exec

Handles ImageKit authentication and configuration.

Configuration Pattern:
    ImageKitConfig uses a check-then-use pattern where from_env() returns None if
    required credentials are missing. This is appropriate for optional plugin
    configuration - if ImageKit credentials are not provided, the plugin is simply
    not activated rather than causing application startup failure.

    Compare with core configs (like SSHConfig) which use a fail-fast pattern that
    raises exceptions during initialization, since core configuration is required
    for the application to function.
"""

import os
from dataclasses import dataclass

from mcp_remote_exec.config.constants import DEFAULT_TRANSFER_TIMEOUT_SECONDS


@dataclass
class ImageKitConfig:
    """Configuration for ImageKit file transfer service"""

    public_key: str
    private_key: str
    url_endpoint: str
    folder: str = "/mcp-remote-exec"  # Default folder for organizing files
    transfer_timeout: int = DEFAULT_TRANSFER_TIMEOUT_SECONDS

    @classmethod
    def from_env(cls) -> "ImageKitConfig | None":
        """
        Create config from environment variables.

        Standardized plugin configuration pattern:
        - Checks if plugin is enabled via ENABLE_IMAGEKIT flag
        - Validates all required credentials are present
        - Returns None if plugin should not be activated (disabled or missing config)
        - Returns validated config instance if all checks pass

        Returns:
            ImageKitConfig if enabled and all required variables are set, None otherwise
        """
        # Check if plugin is enabled first
        if os.getenv("ENABLE_IMAGEKIT", "false").lower() != "true":
            return None

        # Get required credentials
        public_key = os.getenv("IMAGEKIT_PUBLIC_KEY")
        private_key = os.getenv("IMAGEKIT_PRIVATE_KEY")
        url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT")

        # Validate all required credentials are present
        if public_key is None or private_key is None or url_endpoint is None:
            return None

        # Validate credentials are not empty strings
        if not public_key or not private_key or not url_endpoint:
            return None

        # Get optional settings
        transfer_timeout = int(
            os.getenv(
                "IMAGEKIT_TRANSFER_TIMEOUT", str(DEFAULT_TRANSFER_TIMEOUT_SECONDS)
            )
        )
        folder = os.getenv("IMAGEKIT_FOLDER", "/mcp-remote-exec")

        return cls(
            public_key=public_key,
            private_key=private_key,
            url_endpoint=url_endpoint,
            folder=folder,
            transfer_timeout=transfer_timeout,
        )
