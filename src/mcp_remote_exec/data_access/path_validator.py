"""
Path Validation Utilities for SSH MCP Remote Exec

Centralized path validation to prevent directory traversal and ensure file security.
"""

import os
import warnings

from mcp_remote_exec.config.constants import MSG_PATH_TRAVERSAL_ERROR
from mcp_remote_exec.data_access.exceptions import FileValidationError


class PathValidator:
    """Validates file paths for security and correctness"""

    @staticmethod
    def validate_path(
        path: str,
        *,
        check_traversal: bool = True,
        check_exists: bool = False,
        path_type: str = "path",
    ) -> None:
        """
        Validate a file path for security and correctness.

        Args:
            path: The file path to validate
            check_traversal: Whether to check for directory traversal attempts
            check_exists: Whether to check if the path exists
            path_type: Description of path type for error messages (e.g., "local", "remote")

        Raises:
            FileValidationError: If validation fails
        """
        if not path or not path.strip():
            raise FileValidationError(
                f"{path_type.capitalize()} path cannot be empty",
                file_path=path,
                reason="empty_path",
            )

        # Check for directory traversal
        if check_traversal:
            normalized_path = os.path.normpath(path)
            if ".." in normalized_path:
                raise FileValidationError(
                    MSG_PATH_TRAVERSAL_ERROR,
                    file_path=path,
                    reason="directory_traversal",
                )

        # Check if path exists (when required)
        if check_exists and not os.path.exists(path):
            raise FileValidationError(
                f"{path_type.capitalize()} path does not exist: {path}",
                file_path=path,
                reason="path_not_found",
            )

    @staticmethod
    def validate_file_path(
        file_path: str,
        remote_operation: bool = True,
        check_existence: bool = True,
    ) -> None:
        """
        Validate file path for security (prevent directory traversal).

        .. deprecated:: 0.2.0
            Use :meth:`validate_path` instead. This method is maintained for
            backward compatibility but will be removed in a future version.

        Args:
            file_path: The file path to validate
            remote_operation: True for remote paths, False for local paths
            check_existence: Whether to check if local file exists

        Raises:
            FileValidationError: If validation fails
        """
        warnings.warn(
            "PathValidator.validate_file_path() is deprecated and will be removed in a future version. "
            "Use PathValidator.validate_path() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        path_type = "remote" if remote_operation else "local"

        # Always check for directory traversal
        PathValidator.validate_path(
            file_path,
            check_traversal=True,
            check_exists=(check_existence and not remote_operation),
            path_type=path_type,
        )

    @staticmethod
    def check_paths_for_traversal(
        *paths: str,
    ) -> tuple[bool, str | None]:
        """
        Check multiple paths for directory traversal attempts.

        This is a convenience method that validates multiple paths and returns
        a tuple format for easy error handling in service layers. It uses
        validate_path() internally to eliminate duplicate validation logic.

        Args:
            *paths: Variable number of paths to check

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if all paths are safe, False otherwise
            - error_message: None if valid, error description if invalid
        """
        for path in paths:
            try:
                # Use validate_path internally to eliminate duplicate logic
                PathValidator.validate_path(
                    path,
                    check_traversal=True,
                    check_exists=False,
                    path_type="path",
                )
            except FileValidationError as e:
                return False, str(e)
        return True, None
