"""
Exceptions for Configuration Layer

Defines configuration-specific exceptions for SSH MCP Remote Exec.
These exceptions are raised during configuration validation and initialization.
"""


class ConfigError(Exception):
    """
    Raised when configuration validation fails.

    This exception indicates a fatal configuration error that prevents
    the application from starting. Configuration errors should not be caught
    during normal operation - they indicate the application is misconfigured
    and cannot function properly.

    Examples:
        - Missing required configuration (HOST, authentication credentials)
        - Invalid configuration values (negative timeouts, invalid ports)
        - Missing SSH key files
        - Risk acceptance not provided
    """

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        reason: str | None = None,
    ):
        """
        Initialize configuration error with context.

        Args:
            message: Error description message
            config_key: Configuration key that caused error (e.g., "HOST", "SSH_KEY")
            reason: Error reason category (e.g., "missing", "invalid", "not_found")
        """
        self.config_key = config_key
        self.reason = reason
        super().__init__(message)
