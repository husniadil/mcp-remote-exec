"""
Proxmox Plugin for SSH MCP Remote Exec

Provides container management tools for Proxmox VE.
"""

import logging

from fastmcp import FastMCP

from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.plugins.proxmox.config import ProxmoxConfig
from mcp_remote_exec.plugins.proxmox.service import ProxmoxService
from mcp_remote_exec.presentation.service_container import ServiceContainer

_log = logging.getLogger(__name__)


class ProxmoxPlugin(BasePlugin):
    """Plugin for Proxmox VE container management"""

    @property
    def name(self) -> str:
        return "proxmox"

    def is_enabled(self, container: ServiceContainer) -> bool:
        """Check if Proxmox plugin should be activated

        Standardized plugin enablement pattern:
        - Delegates to ProxmoxConfig.from_env() which performs all validation
        - from_env() returns None if plugin is disabled
        - No additional configuration needed (uses SSH creds from SSHConfig)

        Returns:
            True if plugin should be activated, False otherwise
        """
        config = ProxmoxConfig.from_env()
        if config is not None:
            _log.info("Proxmox plugin enabled")
            return True

        _log.debug("Proxmox plugin disabled: ENABLE_PROXMOX not true")
        return False

    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """Register Proxmox container management tools"""
        from mcp_remote_exec.plugins.proxmox.tools import (
            register_proxmox_tools,
            register_proxmox_file_tools,
        )

        # Create Proxmox service once and store in container
        proxmox_service = ProxmoxService(
            command_service=container.command_service,
            file_service=container.file_service,
        )

        # Store service in plugin services for tool access
        container.plugin_services["proxmox"] = proxmox_service

        # Always register container management tools
        register_proxmox_tools(mcp, container)

        # Conditionally register file transfer tools
        # Skip if ImageKit plugin is enabled (it provides unified file transfer)
        imagekit_enabled = "imagekit" in container.enabled_plugins
        if not imagekit_enabled:
            register_proxmox_file_tools(mcp, container)
        else:
            _log.warning(
                "Proxmox file transfer tools NOT registered - ImageKit plugin is active"
            )


__all__ = ["ProxmoxPlugin"]
