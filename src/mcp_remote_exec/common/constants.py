"""
Common Constants for SSH MCP Remote Exec

Shared constants used across all layers of the application.
These are domain-agnostic constants that are used for validation,
limits, and constraints across multiple layers.
"""

# =============================================================================
# Validation Constraints
# =============================================================================

MAX_TIMEOUT = 300
"""Maximum allowed timeout for operations in seconds

This constant is used for input validation across all layers (config, presentation,
plugins) to ensure timeout values don't exceed safe operational limits.
"""
