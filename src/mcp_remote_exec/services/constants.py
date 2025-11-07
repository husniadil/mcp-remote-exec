"""
Constants for SSH MCP Remote Exec Service Layer

Centralized constants for output formatting, file operations, and service configuration.
"""

# Output Formatter Constants
JSON_METADATA_OVERHEAD = 500
"""Reserved space for JSON structure metadata when formatting output"""

MIN_OUTPUT_SPACE = 1000
"""Minimum space allocated for output content after truncation"""

# Temporary File Constants
TEMP_FILE_PREFIX = "/tmp/mcp-proxmox"
"""Prefix for temporary files created during Proxmox operations"""

# Transfer Timeouts
DEFAULT_TRANSFER_TIMEOUT_SECONDS = 3600
"""Default timeout for file transfer operations (1 hour)"""

# Common Error Messages
MSG_CONTAINER_NOT_FOUND = "Use proxmox_list_containers to see available containers"
"""Suggestion message when container is not found"""

MSG_PATH_TRAVERSAL_ERROR = "Path cannot contain '..' (path traversal not allowed)"
"""Error message for path traversal attempts"""
