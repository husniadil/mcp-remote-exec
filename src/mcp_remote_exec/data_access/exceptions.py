"""
Domain-specific exceptions for SSH operations.

Provides custom exceptions that can be caught and handled appropriately
by upper layers while providing context about SSH-specific errors.
"""


class SSHConnectionError(Exception):
    """Raised when SSH connection fails or is lost"""

    def __init__(
        self,
        message: str,
        host_name: str | None = None,
        original_error: Exception | None = None,
    ):
        self.host_name = host_name
        self.original_error = original_error
        super().__init__(message)


class AuthenticationError(SSHConnectionError):
    """Raised when SSH authentication fails"""

    def __init__(
        self,
        message: str,
        host_name: str | None = None,
        username: str | None = None,
    ):
        self.username = username
        super().__init__(message, host_name)


class CommandExecutionError(SSHConnectionError):
    """Raised when SSH command execution fails or times out"""

    def __init__(
        self,
        message: str,
        host_name: str | None = None,
        command: str | None = None,
        exit_code: int | None = None,
    ):
        self.command = command
        self.exit_code = exit_code
        super().__init__(message, host_name)


class SFTPError(SSHConnectionError):
    """Raised when SFTP operations fail"""

    def __init__(
        self,
        message: str,
        host_name: str | None = None,
        operation: str | None = None,
        path: str | None = None,
    ):
        self.operation = operation
        self.path = path
        super().__init__(message, host_name)


class FileValidationError(Exception):
    """Raised when file validation fails (size, path, permissions)"""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        reason: str | None = None,
    ):
        self.file_path = file_path
        self.reason = reason
        super().__init__(message)
