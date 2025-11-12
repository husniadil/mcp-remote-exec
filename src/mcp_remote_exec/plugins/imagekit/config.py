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

        Returns:
            ImageKitConfig if all required variables are set, None otherwise
        """
        public_key = os.getenv("IMAGEKIT_PUBLIC_KEY")
        private_key = os.getenv("IMAGEKIT_PRIVATE_KEY")
        url_endpoint = os.getenv("IMAGEKIT_URL_ENDPOINT")

        # Explicit None checks for type narrowing
        if public_key is None or private_key is None or url_endpoint is None:
            return None

        # Type checker now knows these are str (not None)
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

    def is_enabled(self) -> bool:
        """
        Check if ImageKit plugin is enabled via environment variable.

        Note: This assumes credentials are already validated (via from_env() or validate())
        """
        return os.getenv("ENABLE_IMAGEKIT", "false").lower() == "true"

    def validate(self) -> tuple[bool, str | None]:
        """Validate ImageKit configuration"""
        if not self.public_key:
            return False, "IMAGEKIT_PUBLIC_KEY not set"
        if not self.private_key:
            return False, "IMAGEKIT_PRIVATE_KEY not set"
        if not self.url_endpoint:
            return False, "IMAGEKIT_URL_ENDPOINT not set"

        return True, None
