"""
SSH Configuration Management for SSH MCP Remote Exec

This module provides configuration handling for SSH connections and security settings
with flexible authentication methods.

Configuration Pattern:
    SSHConfig uses a fail-fast initialization pattern where validation errors raise
    ConfigError during __init__(). This is appropriate for core application configuration
    that is required for the system to function. If SSH config is invalid, the application
    cannot start.

    Compare with optional plugin configs (like ImageKitConfig) which use a check-then-use
    pattern where from_env() returns None if config is missing, allowing the plugin to
    be gracefully disabled without stopping the application.
"""

import os
from dataclasses import dataclass

from mcp_remote_exec.common.constants import MAX_TIMEOUT
from mcp_remote_exec.config.exceptions import ConfigError
from mcp_remote_exec.config.constants import (
    DEFAULT_CHARACTER_LIMIT,
    DEFAULT_MAX_FILE_SIZE,
    DEFAULT_TIMEOUT,
    DEFAULT_SSH_PORT,
)


@dataclass
class HostConfig:
    """Configuration for a single SSH host"""

    name: str
    host: str
    port: int
    username: str
    password: str | None = None
    key_path: str | None = None

    def has_auth(self) -> bool:
        """Check if authentication method is configured"""
        return bool(self.password or self.key_path)


@dataclass
class SecurityConfig:
    """Security and limit configurations

    Note: Risk acceptance is validated during SSHConfig initialization,
    not through a separate method call.
    """

    accept_risks: bool
    character_limit: int
    max_file_size: int
    default_timeout: int
    max_timeout: int
    strict_host_key_checking: bool = True


class SSHConfig:
    """Main SSH configuration class"""

    def __init__(self) -> None:
        """Initialize configuration from environment variables"""
        # STEP 1: Check risk acceptance FIRST before any other initialization
        # This is the most critical validation and must fail fast
        accept_risks = os.getenv("I_ACCEPT_RISKS", "false").lower() == "true"
        if not accept_risks:
            raise ConfigError(
                "You must explicitly accept the risks before using this software.\n"
                "Set environment variable: I_ACCEPT_RISKS=true\n\n"
                "By setting this to 'true', you acknowledge that:\n"
                "  - You understand the risks of giving AI system SSH access to your infrastructure\n"
                "  - You are solely responsible for reviewing and approving commands\n"
                "  - You have proper backups and disaster recovery procedures in place\n"
                "  - You will not hold the developer(s) liable for any damages or losses\n\n"
                "See README DISCLAIMER section for full details."
            )

        # STEP 2: Load security settings
        self.security = SecurityConfig(
            accept_risks=accept_risks,
            character_limit=int(
                os.getenv("CHARACTER_LIMIT", str(DEFAULT_CHARACTER_LIMIT))
            ),
            max_file_size=int(os.getenv("MAX_FILE_SIZE", str(DEFAULT_MAX_FILE_SIZE))),
            default_timeout=int(os.getenv("TIMEOUT", str(DEFAULT_TIMEOUT))),
            max_timeout=MAX_TIMEOUT,
            strict_host_key_checking=os.getenv(
                "SSH_STRICT_HOST_KEY_CHECKING", "true"
            ).lower()
            == "true",
        )

        # STEP 3: Load host configuration (may fail if SSH key not found, etc.)
        self.host: HostConfig = self._load_host_config()

        # STEP 4: Validate remaining configuration (authentication, etc.)
        valid, error = self.validate()
        if not valid:
            raise ConfigError(error or "Configuration validation failed")

    def _load_host_config(self) -> HostConfig:
        """Load SSH host configuration from environment variables"""
        host = os.getenv("HOST")
        if not host:
            raise ConfigError(
                "No SSH host configuration found. Set HOST environment variable"
            )

        port = int(os.getenv("SSH_PORT", str(DEFAULT_SSH_PORT)))
        username = os.getenv("SSH_USERNAME", "root")
        key_path = os.getenv("SSH_KEY")

        # Validate SSH key path exists if specified
        if key_path and not os.path.exists(key_path):
            raise ConfigError(
                f"SSH key file not found: {key_path}. "
                "Verify SSH_KEY environment variable points to a valid private key file."
            )

        return HostConfig(
            name="default",
            host=host,
            port=port,
            username=username,
            password=os.getenv("SSH_PASSWORD"),
            key_path=key_path,
        )

    def get_host(self) -> HostConfig:
        """Get the configured SSH host"""
        return self.host

    def validate(self) -> tuple[bool, str | None]:
        """Validate SSH authentication configuration.

        Checks that at least one authentication method (password or SSH key) is configured.

        Note: Risk acceptance and SSH key file existence are validated during __init__,
        before this method is called.

        Returns:
            Tuple of (is_valid, error_message). error_message is None if valid.
        """

        # Validate host has authentication
        if not self.host.has_auth():
            return False, (
                "No authentication configured. "
                "Set SSH_PASSWORD or SSH_KEY environment variable"
            )

        return True, None

    def __repr__(self) -> str:
        """String representation for debugging"""
        host_info = f"{self.host.username}@{self.host.host}:{self.host.port}"
        return (
            f"SSHConfig(host={host_info}, risks_accepted={self.security.accept_risks})"
        )
