"""
Constants for SSH MCP Remote Exec

Centralized constants for the entire application including SSH configuration,
output formatting, file operations, and validation messages.
"""

# =============================================================================
# SSH Configuration Constants
# =============================================================================

DEFAULT_CHARACTER_LIMIT = 25000
"""Default character limit for command output"""

DEFAULT_MAX_FILE_SIZE = 10485760  # 10MB
"""Default maximum file size for transfers"""

DEFAULT_TIMEOUT = 30
"""Default timeout for SSH operations in seconds"""

MAX_TIMEOUT = 300
"""Maximum allowed timeout for SSH operations in seconds"""

DEFAULT_SSH_PORT = 22
"""Default SSH port number"""

# =============================================================================
# Output Formatter Constants
# =============================================================================

JSON_METADATA_OVERHEAD = 500
"""Reserved space for JSON structure metadata when formatting output"""

MIN_OUTPUT_SPACE = 1000
"""Minimum space allocated for output content after truncation"""

# =============================================================================
# Temporary File Constants
# =============================================================================

TEMP_FILE_PREFIX = "/tmp/mcp-proxmox"
"""Prefix for temporary files created during Proxmox operations"""

# =============================================================================
# Transfer Timeouts
# =============================================================================

DEFAULT_TRANSFER_TIMEOUT_SECONDS = 3600
"""Default timeout for file transfer operations (1 hour)"""

# =============================================================================
# Error Messages
# =============================================================================

MSG_PATH_TRAVERSAL_ERROR = "Path cannot contain '..' (path traversal not allowed)"
"""Error message for path traversal attempts"""

MSG_CONTAINER_NOT_FOUND = "Use proxmox_list_containers to see available containers"
"""Suggestion message when container is not found"""
