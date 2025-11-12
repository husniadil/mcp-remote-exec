"""
Constants for Proxmox Plugin

Plugin-specific constants for Proxmox container management operations.
"""

# =============================================================================
# Temporary File Constants
# =============================================================================

TEMP_FILE_PREFIX = "/tmp/mcp-remote-exec"
"""Prefix for temporary files created during Proxmox file transfer operations on remote host.

Note: This is a path on the remote SSH/Proxmox host, not the local MCP server.
We use a hardcoded Unix path because SSH servers and Proxmox VE hosts are always Unix-like systems.
"""

# =============================================================================
# Error Messages
# =============================================================================

MSG_CONTAINER_NOT_FOUND = "Use proxmox_list_containers to see available containers"
"""Suggestion message when container is not found"""
