"""
ImageKit Plugin for SSH MCP Remote Exec

Provides two-phase file transfer functionality via ImageKit for HTTP gateway scenarios.
"""

import logging

from fastmcp import FastMCP
from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig
from mcp_remote_exec.plugins.imagekit.constants import MSG_CONFIG_NOT_FOUND
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

        Standardized plugin enablement pattern:
        - Delegates to ImageKitConfig.from_env() which performs all validation
        - from_env() returns None if plugin is disabled or misconfigured
        - Caches config for use in register_tools()

        Returns:
            True if plugin should be activated, False otherwise
        """
        # Cache config to avoid redundant creation in register_tools()
        self._config = ImageKitConfig.from_env()

        if self._config is None:
            _log.debug(
                "ImageKit plugin disabled: ENABLE_IMAGEKIT not true or credentials missing"
            )
            return False

        _log.info("ImageKit plugin enabled")
        return True

    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """Register ImageKit tools and setup service"""
        # Use cached config from is_enabled() to avoid redundant creation
        if not self._config:
            _log.error(MSG_CONFIG_NOT_FOUND)
            return

        # Create ImageKit service
        imagekit_service = ImageKitService(
            config=self._config,
            command_service=container.command_service,
            file_service=container.file_service,
            enabled_plugins=container.enabled_plugins,
        )

        # Store service in plugin services for tool access
        container.plugin_services["imagekit"] = imagekit_service

        # Register tools
        register_imagekit_tools(mcp, container)


__all__ = ["ImageKitPlugin"]
