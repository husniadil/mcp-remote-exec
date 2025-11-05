"""
Proxmox Plugin for SSH MCP Remote Exec

Provides container management tools for Proxmox VE.
"""

import os
import logging
from fastmcp import FastMCP
from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.presentation.service_container import ServiceContainer

_log = logging.getLogger(__name__)


class ProxmoxPlugin(BasePlugin):
    """Plugin for Proxmox VE container management"""

    @property
    def name(self) -> str:
        return "proxmox"

    def is_enabled(self, container: ServiceContainer) -> bool:
        """Check if Proxmox plugin is enabled via ENABLE_PROXMOX env var"""
        enabled = os.getenv("ENABLE_PROXMOX", "false").lower() == "true"
        if enabled:
            _log.info("Proxmox plugin enabled")
        return enabled

    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """Register Proxmox container management tools"""
        from mcp_remote_exec.plugins.proxmox.tools import register_proxmox_tools

        register_proxmox_tools(mcp, container)
        _log.info("Proxmox tools registered")


__all__ = ["ProxmoxPlugin"]
