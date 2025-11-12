"""
Common Enums for SSH MCP Remote Exec

Shared enumerations used across multiple layers.
"""

from enum import Enum


class ResponseFormat(str, Enum):
    """Output format for tool responses"""

    TEXT = "text"
    JSON = "json"
