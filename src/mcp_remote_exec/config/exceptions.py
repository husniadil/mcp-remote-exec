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

    pass
