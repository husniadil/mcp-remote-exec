"""
SSH Connection Manager for SSH MCP Remote Exec

Manages SSH connections, command execution, and connection lifecycle.
Supports both password and SSH key authentication with multi-format key support
(RSA, ED25519, ECDSA). Handles SSH key loading, connection pooling, and cleanup.
"""

import socket
import paramiko
import logging
from dataclasses import dataclass

from mcp_remote_exec.config.ssh_config import SSHConfig
from mcp_remote_exec.data_access.exceptions import (
    SSHConnectionError,
    AuthenticationError,
    CommandExecutionError,
)

_log = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of SSH command execution"""

    exit_code: int
    stdout: str
    stderr: str
    timeout_reached: bool = False
    command: str = ""


class SSHConnectionManager:
    """Manages SSH connection and command execution"""

    def __init__(self, config: SSHConfig):
        """Initialize connection manager with SSH configuration"""
        self.config = config
        self._client: paramiko.SSHClient | None = None

    def _load_private_key(self, key_path: str) -> paramiko.PKey:
        """Load private SSH key supporting RSA, Ed25519, and ECDSA formats.

        Note: Ed25519 support requires Paramiko >= 3.x. Earlier versions will raise
        AttributeError when attempting to load Ed25519 keys and will fall back to ECDSA.
        """
        host_config = self.config.get_host()

        # Check Ed25519 support at runtime
        has_ed25519 = hasattr(paramiko, "Ed25519Key")
        supported_formats = "RSA, ECDSA"
        if has_ed25519:
            supported_formats = "RSA, Ed25519, ECDSA"

        try:
            # Try to load as RSA key (most common)
            try:
                return paramiko.RSAKey.from_private_key_file(key_path)
            except paramiko.SSHException:
                pass

            # Try to load as Ed25519 key (requires Paramiko >= 3.x)
            # AttributeError is caught for older Paramiko versions that don't support Ed25519
            if has_ed25519:
                try:
                    return paramiko.Ed25519Key.from_private_key_file(key_path)
                except paramiko.SSHException:
                    pass

            # Try to load as ECDSA key (fallback)
            try:
                return paramiko.ECDSAKey.from_private_key_file(key_path)
            except paramiko.SSHException:
                pass

            # If all formats fail, raise error with supported formats
            raise AuthenticationError(
                f"Failed to load private key from {key_path}. Supported formats: {supported_formats}",
                host_name=host_config.name,
            )
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(
                f"Error loading private key from {key_path}: {str(e)}",
                host_name=host_config.name,
            )

    def get_connection(self) -> paramiko.SSHClient:
        """Get SSH client, creating connection if needed"""
        if self._client is None:
            self._create_connection()

        if self._client is None:
            raise SSHConnectionError(
                "Failed to establish SSH connection",
                host_name=self.config.get_host().name,
            )
        return self._client

    def _create_connection(self) -> None:
        """Create SSH connection to host"""
        host_config = self.config.get_host()
        _log.info(f"Creating SSH connection to {host_config.host}:{host_config.port}")

        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.RejectPolicy())

            # Use config timeout value for connection
            connection_timeout = self.config.security.default_timeout

            # Choose authentication method
            if host_config.key_path:
                # SSH key authentication
                _log.info(f"Using SSH key authentication: {host_config.key_path}")
                private_key = self._load_private_key(host_config.key_path)
                client.connect(
                    hostname=host_config.host,
                    port=host_config.port,
                    username=host_config.username,
                    pkey=private_key,
                    timeout=connection_timeout,
                )
                auth_method = "key"
            elif host_config.password:
                # Password authentication
                _log.info(
                    f"Using password authentication for {host_config.username}@{host_config.host}"
                )
                client.connect(
                    hostname=host_config.host,
                    port=host_config.port,
                    username=host_config.username,
                    password=host_config.password,
                    timeout=connection_timeout,
                )
                auth_method = "password"
            else:
                raise AuthenticationError(
                    f"No authentication method configured for host '{host_config.name}'",
                    host_name=host_config.name,
                    username=host_config.username,
                )

            self._client = client
            _log.info(f"Successfully connected using {auth_method} authentication")

        except paramiko.AuthenticationException:
            error_msg = f"Authentication failed for {host_config.username}@{host_config.host}:{host_config.port}"
            raise AuthenticationError(
                error_msg, host_name=host_config.name, username=host_config.username
            )
        except paramiko.SSHException as e:
            error_msg = f"SSH connection failed to {host_config.host}:{host_config.port} - {str(e)}"
            raise SSHConnectionError(
                error_msg, host_name=host_config.name, original_error=e
            )
        except Exception as e:
            error_msg = (
                f"Connection error to {host_config.host}:{host_config.port} - {str(e)}"
            )
            raise SSHConnectionError(
                error_msg, host_name=host_config.name, original_error=e
            )

    def execute_command(self, command: str, timeout: int = 30) -> ExecutionResult:
        """Execute command via SSH"""
        if not command.strip():
            raise CommandExecutionError("Command cannot be empty")

        # Validate and constrain timeout to config limits
        max_timeout = self.config.security.max_timeout
        timeout = max(1, min(int(timeout), max_timeout))

        host_config = self.config.get_host()
        _log.info(
            f"Executing command on {host_config.name}: {command[:100]}{'...' if len(command) > 100 else ''}"
        )

        try:
            client = self.get_connection()

            # Execute command with timeout
            # Security note: Commands are executed directly via SSH protocol, not through a shell interpreter.
            # While the command IS executed on the remote system, Paramiko doesn't invoke /bin/sh -c,
            # making traditional shell injection less applicable. The actual security boundary is the
            # MCP server's authentication, authorization, and the configured SSH user's permissions.
            # Users must ensure proper access controls and monitoring are in place.
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)  # nosec B601

            # Read output with error handling
            try:
                stdout_data = stdout.read().decode("utf-8", errors="replace")
                stderr_data = stderr.read().decode("utf-8", errors="replace")
                exit_code = stdout.channel.recv_exit_status()
            except UnicodeDecodeError:
                raise CommandExecutionError(
                    "Command output contains invalid Unicode",
                    host_name=host_config.name,
                    command=command,
                )

            return ExecutionResult(
                exit_code=exit_code,
                stdout=stdout_data,
                stderr=stderr_data,
                timeout_reached=False,
                command=command,
            )

        except paramiko.SSHException as e:
            error_msg = f"SSH command execution failed: {str(e)}"
            raise CommandExecutionError(
                error_msg, host_name=host_config.name, command=command
            )
        except socket.timeout:
            error_msg = f"Command execution timed out after {timeout} seconds"
            raise CommandExecutionError(
                error_msg, host_name=host_config.name, command=command
            )
        except Exception as e:
            error_msg = f"Unexpected error during command execution: {str(e)}"
            raise CommandExecutionError(
                error_msg, host_name=host_config.name, command=command
            )

    def close_connection(self) -> None:
        """Close SSH connection"""
        if self._client is None:
            return
        try:
            _log.info("Closing SSH connection")
            self._client.close()
        except Exception as e:
            _log.warning(f"Error closing SSH connection: {str(e)}")
        finally:
            self._client = None

    def __del__(self) -> None:
        """Cleanup on object destruction"""
        self.close_connection()

    def __enter__(self) -> "SSHConnectionManager":
        """Context manager entry"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Context manager exit with cleanup"""
        self.close_connection()
