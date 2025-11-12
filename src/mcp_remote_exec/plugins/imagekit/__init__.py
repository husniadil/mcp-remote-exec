"""
ImageKit Plugin for SSH MCP Remote Exec

Provides two-phase file transfer functionality via ImageKit for HTTP gateway scenarios.
"""

import logging

from fastmcp import FastMCP
from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig
from mcp_remote_exec.plugins.imagekit.service import ImageKitService
from mcp_remote_exec.plugins.imagekit.tools import register_imagekit_tools

_log = logging.getLogger(__name__)


class ImageKitPlugin(BasePlugin):
    """Plugin for ImageKit-based file transfers"""

    def __init__(self) -> None:
        """Initialize plugin with cached config"""
        self._config: ImageKitConfig | None = None

    @property
    def name(self) -> str:
        return "imagekit"

    def is_enabled(self, container: ServiceContainer) -> bool:
        """Check if ImageKit plugin should be activated

        Uses a standardized enablement pattern consistent with other plugins:
        1. Check ENABLE_IMAGEKIT environment variable
        2. Validate plugin-specific configuration (credentials)
        """
        # Cache config to avoid redundant creation in register_tools()
        self._config = ImageKitConfig.from_env()

        if not self._config:
            _log.debug("ImageKit plugin disabled: credentials not configured")
            return False

        if not self._config.is_enabled():
            _log.debug("ImageKit plugin disabled: ENABLE_IMAGEKIT not set to true")
            return False

        valid, error = self._config.validate()
        if not valid:
            _log.warning(f"ImageKit plugin disabled: {error}")
            return False

        _log.info("ImageKit plugin enabled")
        return True

    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """Register ImageKit tools and setup service"""
        # Use cached config from is_enabled() to avoid redundant creation
        if not self._config:
            _log.error("ImageKit configuration not found")
            return

        # Create ImageKit service
        imagekit_service = ImageKitService(
            config=self._config,
            command_service=container.command_service,
            sftp_manager=container.sftp_manager,
            enabled_plugins=container.enabled_plugins,
        )

        # Store service in plugin services for tool access
        container.plugin_services["imagekit"] = imagekit_service

        # Register tools
        register_imagekit_tools(mcp, container)


__all__ = ["ImageKitPlugin"]
