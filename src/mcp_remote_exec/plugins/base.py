"""
Base Plugin Interface for SSH MCP Remote Exec

Defines the contract that all plugins must implement.
"""

from abc import ABC, abstractmethod
from fastmcp import FastMCP
from mcp_remote_exec.presentation.service_container import ServiceContainer


class BasePlugin(ABC):
    """Abstract base class for MCP plugins"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin identifier (e.g., 'proxmox', 'docker')"""
        pass

    @abstractmethod
    def is_enabled(self, container: ServiceContainer) -> bool:
        """
        Check if plugin should be activated based on configuration.

        Args:
            container: Service container with config and services

        Returns:
            True if plugin should register its tools, False otherwise
        """
        pass

    @abstractmethod
    def register_tools(self, mcp: FastMCP, container: ServiceContainer) -> None:
        """
        Register plugin's MCP tools.

        Args:
            mcp: FastMCP server instance to register tools with
            container: Service container for accessing core services
        """
        pass
