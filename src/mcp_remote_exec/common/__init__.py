"""
Common Layer - Shared code across all layers

This layer contains shared utilities, enums, and validators that are used
across multiple layers (presentation, plugins, etc.) to avoid circular
dependencies and maintain clean architecture.
"""

from mcp_remote_exec.common.enums import ResponseFormat
from mcp_remote_exec.common.validators import validate_octal_permissions

__all__ = [
    "ResponseFormat",
    "validate_octal_permissions",
]
