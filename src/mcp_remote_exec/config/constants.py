"""
Constants for SSH MCP Remote Exec

Centralized constants for the core application including SSH configuration,
output formatting, and file operations.
"""

# Import validation constants from common layer
from mcp_remote_exec.common.constants import MAX_TIMEOUT

# =============================================================================
# SSH Configuration Constants
# =============================================================================

DEFAULT_CHARACTER_LIMIT = 25000
"""Default character limit for command output"""

DEFAULT_MAX_FILE_SIZE = 10485760  # 10MB
"""Default maximum file size for transfers"""

DEFAULT_TIMEOUT = 30
"""Default timeout for SSH operations in seconds"""

# MAX_TIMEOUT is imported from common.constants and re-exported here
# for backward compatibility with existing imports

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
# Transfer Timeouts
# =============================================================================

DEFAULT_TRANSFER_TIMEOUT_SECONDS = 3600
"""Default timeout for file transfer operations (1 hour)"""

# =============================================================================
# Path Validation Messages
# =============================================================================

MSG_PATH_TRAVERSAL_ERROR = "Path cannot contain '..' (path traversal not allowed)"
"""Error message for path traversal attempts"""

# =============================================================================
# Public API
# =============================================================================

__all__ = [
    # Imported and re-exported from common layer
    "MAX_TIMEOUT",
    # SSH Configuration
    "DEFAULT_CHARACTER_LIMIT",
    "DEFAULT_MAX_FILE_SIZE",
    "DEFAULT_TIMEOUT",
    "DEFAULT_SSH_PORT",
    # Output Formatting
    "JSON_METADATA_OVERHEAD",
    "MIN_OUTPUT_SPACE",
    # Transfer Timeouts
    "DEFAULT_TRANSFER_TIMEOUT_SECONDS",
    # Path Validation Messages
    "MSG_PATH_TRAVERSAL_ERROR",
]
