"""
Plugin Registry for SSH MCP Remote Exec

Handles plugin discovery and registration.
"""

import logging
from fastmcp import FastMCP
from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.presentation.service_container import ServiceContainer

_log = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for discovering and managing plugins"""

    def __init__(self) -> None:
        """Initialize plugin registry"""
        self.plugins: list[BasePlugin] = []

    def discover_plugins(self) -> None:
        """
        Discover available plugins.

        Currently uses explicit registration. In future, could use
        entry points or directory scanning for dynamic discovery.
        """
        # Import and register known plugins
        try:
            from mcp_remote_exec.plugins.proxmox import ProxmoxPlugin

            self.plugins.append(ProxmoxPlugin())
            _log.debug("Discovered Proxmox plugin")
        except ImportError:
            _log.debug("Proxmox plugin not available")

        try:
            from mcp_remote_exec.plugins.imagekit import ImageKitPlugin

            self.plugins.append(ImageKitPlugin())
            _log.debug("Discovered ImageKit plugin")
        except ImportError:
            _log.debug("ImageKit plugin not available")

    def register_all(self, mcp: FastMCP, container: ServiceContainer) -> list[str]:
        """
        Register all enabled plugins with the MCP server.

        Args:
            mcp: FastMCP server instance
            container: Service container with config and services

        Returns:
            List of activated plugin names
        """
        # Pre-scan: Determine which plugins will be enabled
        # This allows plugins to coordinate during registration
        for plugin in self.plugins:
            if plugin.is_enabled(container):
                container.enabled_plugins.add(plugin.name)
                _log.debug(f"Plugin {plugin.name} will be enabled")

        # Check for plugin coordination needs
        self._check_plugin_coordination(container)

        activated = []

        # Now register the enabled plugins
        for plugin in self.plugins:
            try:
                if plugin.name in container.enabled_plugins:
                    _log.info(f"Activating plugin: {plugin.name}")
                    plugin.register_tools(mcp, container)
                    activated.append(plugin.name)
                else:
                    _log.debug(f"Plugin {plugin.name} is disabled")
            except Exception as e:
                _log.error(f"Failed to register plugin {plugin.name}: {e}")
                # Remove from enabled set if registration failed
                container.enabled_plugins.discard(plugin.name)

        return activated

    def _check_plugin_coordination(self, container: ServiceContainer) -> None:
        """
        Check for plugin coordination and potential conflicts.

        Logs warnings about tool replacements and conflicts.
        """
        # Check if both Proxmox and ImageKit are enabled
        proxmox_enabled = "proxmox" in container.enabled_plugins
        imagekit_enabled = "imagekit" in container.enabled_plugins

        if proxmox_enabled and imagekit_enabled:
            _log.warning(
                "Both Proxmox and ImageKit plugins are enabled. "
                "Proxmox file transfer tools will be disabled in favor of ImageKit."
            )

    def discover_and_register(
        self, mcp: FastMCP, container: ServiceContainer
    ) -> list[str]:
        """
        Convenience method to discover and register plugins in one call.

        Args:
            mcp: FastMCP server instance
            container: Service container with config and services

        Returns:
            List of activated plugin names
        """
        self.discover_plugins()
        return self.register_all(mcp, container)
