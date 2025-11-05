"""
Plugin system for SSH MCP Remote Exec

Provides extensible plugin architecture for domain-specific operations.
"""

from mcp_remote_exec.plugins.base import BasePlugin
from mcp_remote_exec.plugins.registry import PluginRegistry

__all__ = ["BasePlugin", "PluginRegistry"]
