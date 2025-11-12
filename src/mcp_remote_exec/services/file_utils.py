"""
File Utilities for Services Layer

Provides utility functions for file operations used by service classes.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_remote_exec.services.command_service import CommandService

_log = logging.getLogger(__name__)


def cleanup_temp_file(command_service: "CommandService", temp_path: str) -> None:
    """Best-effort cleanup of temporary files on remote host.

    This function attempts to remove a temporary file from the remote host.
    All errors are silently ignored as this is best-effort cleanup that should
    not cause the main operation to fail.

    Args:
        command_service: CommandService instance for executing cleanup command
        temp_path: Absolute path to temporary file to remove on remote host

    Note:
        - Uses `rm -f` which never fails (force remove, ignore nonexistent)
        - Executes with 5-second timeout
        - All exceptions are caught and ignored (best-effort)
        - Designed for cleanup in error paths and success paths

    Example:
        >>> cleanup_temp_file(cmd_service, "/tmp/upload-abc123.tmp")
        # File is removed if exists, errors are silently ignored
    """
    try:
        command_service.execute_command_raw(f"rm -f {temp_path}", 5)
        _log.debug(f"Cleaned up temp file: {temp_path}")
    except Exception as e:  # nosec B110 - Intentionally broad for best-effort cleanup
        # Best-effort cleanup: ignore all errors
        # This is expected behavior - cleanup should never cause operation failure
        _log.debug(f"Temp file cleanup failed (ignored): {temp_path} - {e}")
        pass
