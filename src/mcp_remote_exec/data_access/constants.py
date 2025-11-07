"""
Constants for Data Access Layer

This module re-exports constants from the centralized constants module for
backward compatibility. New code should import directly from mcp_remote_exec.constants.
"""

from mcp_remote_exec.constants import MSG_PATH_TRAVERSAL_ERROR

__all__ = ["MSG_PATH_TRAVERSAL_ERROR"]
