"""
Constants for Proxmox Plugin

Plugin-specific constants for Proxmox container management operations.
"""

import os
import tempfile

# =============================================================================
# Temporary File Constants
# =============================================================================

TEMP_FILE_PREFIX = os.path.join(tempfile.gettempdir(), "mcp-remote-exec")
"""Prefix for temporary files created during Proxmox file transfer operations"""

# =============================================================================
# Error Messages
# =============================================================================

MSG_CONTAINER_NOT_FOUND = "Use proxmox_list_containers to see available containers"
"""Suggestion message when container is not found"""
