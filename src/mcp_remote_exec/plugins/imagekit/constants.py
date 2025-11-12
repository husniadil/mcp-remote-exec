"""
Constants for ImageKit Plugin

Plugin-specific constants for ImageKit file transfer operations.

Note on constant imports:
    This plugin imports DEFAULT_TRANSFER_TIMEOUT_SECONDS from core config.constants
    because it's a shared application-wide setting. Plugin-specific constants that
    are unique to ImageKit functionality are defined here.
"""

# =============================================================================
# Temporary File Constants
# =============================================================================

TEMP_FILE_PREFIX_UPLOAD = "/tmp/mcp-imagekit-upload"
"""Prefix for temporary files created during ImageKit upload operations on remote host"""

TEMP_FILE_PREFIX_DOWNLOAD = "/tmp/mcp-imagekit-download"
"""Prefix for temporary files created during ImageKit download operations on remote host"""

# =============================================================================
# Error Messages
# =============================================================================

MSG_PROXMOX_REQUIRED = "Container file transfers require Proxmox plugin to be enabled"
"""Error message when container operations are attempted without Proxmox plugin"""

MSG_PROXMOX_ENABLE_SUGGESTION = "Set ENABLE_PROXMOX=true in your .env file to use container features (ctid parameter)"
"""Suggestion message for enabling Proxmox plugin"""

MSG_TRANSFER_NOT_FOUND = "Transfer not found or expired"
"""Error message when transfer ID is not found"""

MSG_CONFIG_NOT_FOUND = "ImageKit configuration not found"
"""Error message when ImageKit config is missing"""
