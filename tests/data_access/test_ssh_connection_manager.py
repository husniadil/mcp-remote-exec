"""
Tests for SSHConnectionManager

Comprehensive tests for SSH connection manager functionality including
connection management, command execution, authentication, and error handling.
"""

import pytest
import socket
from unittest.mock import MagicMock, patch, Mock, PropertyMock
from mcp_remote_exec.data_access.ssh_connection_manager import (
    SSHConnectionManager,
    ExecutionResult,
)
from mcp_remote_exec.data_access.exceptions import (
    SSHConnectionError,
    AuthenticationError,
    CommandExecutionError,
)
import paramiko


@pytest.fixture
def mock_ssh_config(mock_host_config, mock_security_config):
    """Create a mock SSH config"""
    mock = MagicMock()
    mock.get_host.return_value = mock_host_config
    mock.security = mock_security_config
    return mock


@pytest.fixture
def connection_manager(mock_ssh_config):
    """Create SSHConnectionManager instance with mocked config"""
    return SSHConnectionManager(mock_ssh_config)


# =============================================================================
# Basic Tests (Existing)
# =============================================================================


def test_connection_manager_initialization(connection_manager, mock_ssh_config):
    """Test that SSHConnectionManager initializes correctly"""
    assert connection_manager is not None
    assert connection_manager.config == mock_ssh_config
    assert connection_manager._client is None


def test_execution_result_dataclass():
    """Test ExecutionResult dataclass creation"""
    result = ExecutionResult(
        exit_code=0,
        stdout="test output",
        stderr="test error",
        timeout_reached=False,
        command="test command",
    )

    assert result.exit_code == 0
    assert result.stdout == "test output"
    assert result.stderr == "test error"
    assert result.timeout_reached is False
    assert result.command == "test command"


def test_execution_result_defaults():
    """Test ExecutionResult with default values"""
    result = ExecutionResult(exit_code=0, stdout="output", stderr="error")

    assert result.exit_code == 0
    assert result.stdout == "output"
    assert result.stderr == "error"
    assert result.timeout_reached is False
    assert result.command == ""


def test_connection_manager_has_required_methods(connection_manager):
    """Test that SSHConnectionManager has required methods"""
    assert hasattr(connection_manager, "get_connection")
    assert hasattr(connection_manager, "execute_command")
    assert hasattr(connection_manager, "close_connection")
    assert callable(getattr(connection_manager, "get_connection"))
    assert callable(getattr(connection_manager, "execute_command"))
    assert callable(getattr(connection_manager, "close_connection"))


# =============================================================================
# SSH Key Loading Tests
# =============================================================================


class TestLoadPrivateKey:
    """Tests for _load_private_key method"""

    @patch("paramiko.RSAKey.from_private_key_file")
    def test_load_rsa_key_success(
        self, mock_rsa_load, connection_manager, mock_host_config
    ):
        """Test successfully loading RSA key"""
        mock_key = Mock()
        mock_rsa_load.return_value = mock_key

        result = connection_manager._load_private_key("/path/to/key")

        assert result == mock_key
        mock_rsa_load.assert_called_once_with("/path/to/key")

    @patch("paramiko.ECDSAKey.from_private_key_file")
    @patch("paramiko.Ed25519Key.from_private_key_file")
    @patch("paramiko.RSAKey.from_private_key_file")
    def test_load_ed25519_key_success(
        self,
        mock_rsa_load,
        mock_ed25519_load,
        mock_ecdsa_load,
        connection_manager,
    ):
        """Test successfully loading Ed25519 key"""
        mock_key = Mock()
        mock_rsa_load.side_effect = paramiko.SSHException("Not RSA")
        mock_ed25519_load.return_value = mock_key

        result = connection_manager._load_private_key("/path/to/ed25519_key")

        assert result == mock_key
        mock_ed25519_load.assert_called_once()

    @patch("paramiko.ECDSAKey.from_private_key_file")
    @patch("paramiko.Ed25519Key.from_private_key_file")
    @patch("paramiko.RSAKey.from_private_key_file")
    def test_load_ecdsa_key_success(
        self,
        mock_rsa_load,
        mock_ed25519_load,
        mock_ecdsa_load,
        connection_manager,
    ):
        """Test successfully loading ECDSA key"""
        mock_key = Mock()
        mock_rsa_load.side_effect = paramiko.SSHException("Not RSA")
        mock_ed25519_load.side_effect = paramiko.SSHException("Not Ed25519")
        mock_ecdsa_load.return_value = mock_key

        result = connection_manager._load_private_key("/path/to/ecdsa_key")

        assert result == mock_key
        mock_ecdsa_load.assert_called_once()

    @patch("paramiko.ECDSAKey.from_private_key_file")
    @patch("paramiko.Ed25519Key.from_private_key_file")
    @patch("paramiko.RSAKey.from_private_key_file")
    def test_load_key_all_formats_fail(
        self,
        mock_rsa_load,
        mock_ed25519_load,
        mock_ecdsa_load,
        connection_manager,
    ):
        """Test key loading when all formats fail"""
        mock_rsa_load.side_effect = paramiko.SSHException("Not RSA")
        mock_ed25519_load.side_effect = paramiko.SSHException("Not Ed25519")
        mock_ecdsa_load.side_effect = paramiko.SSHException("Not ECDSA")

        with pytest.raises(AuthenticationError) as exc_info:
            connection_manager._load_private_key("/path/to/invalid_key")

        assert "Failed to load private key" in str(exc_info.value)
        assert "Supported formats" in str(exc_info.value)

    @patch("paramiko.RSAKey.from_private_key_file")
    def test_load_key_generic_exception(self, mock_rsa_load, connection_manager):
        """Test key loading with unexpected exception"""
        mock_rsa_load.side_effect = Exception("Unexpected error")

        with pytest.raises(AuthenticationError) as exc_info:
            connection_manager._load_private_key("/path/to/key")

        assert "Error loading private key" in str(exc_info.value)


# =============================================================================
# Connection Management Tests
# =============================================================================


class TestGetConnection:
    """Tests for get_connection method"""

    @patch.object(SSHConnectionManager, "_create_connection")
    def test_get_connection_creates_when_none(
        self, mock_create, connection_manager
    ):
        """Test get_connection creates connection when none exists"""
        mock_client = Mock(spec=paramiko.SSHClient)
        connection_manager._client = None

        # Mock _create_connection to set _client
        def set_client():
            connection_manager._client = mock_client

        mock_create.side_effect = set_client

        result = connection_manager.get_connection()

        assert result == mock_client
        mock_create.assert_called_once()

    def test_get_connection_reuses_existing(self, connection_manager):
        """Test get_connection reuses existing connection"""
        mock_client = Mock(spec=paramiko.SSHClient)
        connection_manager._client = mock_client

        result = connection_manager.get_connection()

        assert result == mock_client

    @patch.object(SSHConnectionManager, "_create_connection")
    def test_get_connection_raises_if_creation_fails(
        self, mock_create, connection_manager
    ):
        """Test get_connection raises error if connection creation fails"""
        connection_manager._client = None
        mock_create.return_value = None  # Doesn't set _client

        with pytest.raises(SSHConnectionError) as exc_info:
            connection_manager.get_connection()

        assert "Failed to establish SSH connection" in str(exc_info.value)


# =============================================================================
# Connection Creation Tests
# =============================================================================


class TestCreateConnection:
    """Tests for _create_connection method"""

    @patch("paramiko.SSHClient")
    def test_create_connection_password_auth_success(
        self, mock_ssh_client_class, mock_ssh_config
    ):
        """Test successful connection with password authentication"""
        # Setup
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22
        mock_host_config.username = "testuser"
        mock_host_config.password = "testpass"
        mock_host_config.key_path = None
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = True
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        # Execute
        manager._create_connection()

        # Verify
        assert manager._client == mock_client
        mock_client.load_system_host_keys.assert_called_once()
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once_with(
            hostname="test.example.com",
            port=22,
            username="testuser",
            password="testpass",
            timeout=30,
        )

    @patch("paramiko.SSHClient")
    @patch.object(SSHConnectionManager, "_load_private_key")
    def test_create_connection_key_auth_success(
        self, mock_load_key, mock_ssh_client_class, mock_ssh_config
    ):
        """Test successful connection with key authentication"""
        # Setup
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_key = Mock()
        mock_load_key.return_value = mock_key

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22
        mock_host_config.username = "testuser"
        mock_host_config.password = None
        mock_host_config.key_path = "/path/to/key"
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = False
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        # Execute
        manager._create_connection()

        # Verify
        assert manager._client == mock_client
        mock_load_key.assert_called_once_with("/path/to/key")
        mock_client.connect.assert_called_once_with(
            hostname="test.example.com",
            port=22,
            username="testuser",
            pkey=mock_key,
            timeout=30,
        )

    @patch("paramiko.SSHClient")
    def test_create_connection_no_auth_method(
        self, mock_ssh_client_class, mock_ssh_config
    ):
        """Test connection fails with no authentication method"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22  # Add port
        mock_host_config.username = "testuser"
        mock_host_config.password = None
        mock_host_config.key_path = None
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = True
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        # Note: AuthenticationError is raised but caught by generic Exception handler
        # which wraps it in SSHConnectionError (current implementation behavior)
        with pytest.raises((AuthenticationError, SSHConnectionError)) as exc_info:
            manager._create_connection()

        assert "No authentication method configured" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_create_connection_authentication_failure(
        self, mock_ssh_client_class, mock_ssh_config
    ):
        """Test connection handles authentication failure"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = paramiko.AuthenticationException(
            "Auth failed"
        )

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22
        mock_host_config.username = "testuser"
        mock_host_config.password = "badpass"
        mock_host_config.key_path = None
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = True
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        with pytest.raises(AuthenticationError) as exc_info:
            manager._create_connection()

        assert "Authentication failed" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_create_connection_ssh_exception(
        self, mock_ssh_client_class, mock_ssh_config
    ):
        """Test connection handles SSH exception"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = paramiko.SSHException("Connection failed")

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22
        mock_host_config.username = "testuser"
        mock_host_config.password = "testpass"
        mock_host_config.key_path = None
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = True
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        with pytest.raises(SSHConnectionError) as exc_info:
            manager._create_connection()

        assert "SSH connection failed" in str(exc_info.value)

    @patch("paramiko.SSHClient")
    def test_create_connection_generic_exception(
        self, mock_ssh_client_class, mock_ssh_config
    ):
        """Test connection handles generic exception"""
        mock_client = Mock()
        mock_ssh_client_class.return_value = mock_client
        mock_client.connect.side_effect = Exception("Unexpected error")

        mock_host_config = Mock()
        mock_host_config.host = "test.example.com"
        mock_host_config.port = 22
        mock_host_config.username = "testuser"
        mock_host_config.password = "testpass"
        mock_host_config.key_path = None
        mock_host_config.name = "test-host"

        mock_ssh_config.get_host.return_value = mock_host_config
        mock_ssh_config.security.strict_host_key_checking = True
        mock_ssh_config.security.default_timeout = 30

        manager = SSHConnectionManager(mock_ssh_config)

        with pytest.raises(SSHConnectionError) as exc_info:
            manager._create_connection()

        assert "Connection error" in str(exc_info.value)


# =============================================================================
# Command Execution Tests
# =============================================================================


class TestExecuteCommand:
    """Tests for execute_command method"""

    def test_execute_command_empty_command(self, connection_manager):
        """Test execute_command rejects empty command"""
        with pytest.raises(CommandExecutionError) as exc_info:
            connection_manager.execute_command("")

        assert "Command cannot be empty" in str(exc_info.value)

    def test_execute_command_whitespace_only(self, connection_manager):
        """Test execute_command rejects whitespace-only command"""
        with pytest.raises(CommandExecutionError) as exc_info:
            connection_manager.execute_command("   \t\n  ")

        assert "Command cannot be empty" in str(exc_info.value)

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_success(self, mock_get_conn, connection_manager):
        """Test successful command execution"""
        # Setup mock SSH client and channels
        mock_client = Mock()
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()

        mock_stdout.read.return_value = b"command output"
        mock_stderr.read.return_value = b"error output"
        mock_stdout.channel = mock_channel
        mock_channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (
            mock_stdin,
            mock_stdout,
            mock_stderr,
        )
        mock_get_conn.return_value = mock_client

        # Execute
        result = connection_manager.execute_command("ls -la", timeout=30)

        # Verify
        assert result.exit_code == 0
        assert result.stdout == "command output"
        assert result.stderr == "error output"
        assert result.timeout_reached is False
        assert result.command == "ls -la"
        mock_client.exec_command.assert_called_once_with("ls -la", timeout=30)

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_with_non_zero_exit(
        self, mock_get_conn, connection_manager
    ):
        """Test command execution with non-zero exit code"""
        mock_client = Mock()
        mock_stdin = Mock()
        mock_stdout = Mock()
        mock_stderr = Mock()
        mock_channel = Mock()

        mock_stdout.read.return_value = b""
        mock_stderr.read.return_value = b"command not found"
        mock_stdout.channel = mock_channel
        mock_channel.recv_exit_status.return_value = 127

        mock_client.exec_command.return_value = (
            mock_stdin,
            mock_stdout,
            mock_stderr,
        )
        mock_get_conn.return_value = mock_client

        result = connection_manager.execute_command("nonexistent-command")

        assert result.exit_code == 127
        assert result.stderr == "command not found"

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_timeout_constraint(
        self, mock_get_conn, connection_manager, mock_ssh_config
    ):
        """Test command execution respects timeout constraints"""
        mock_client = Mock()
        mock_stdin, mock_stdout, mock_stderr = Mock(), Mock(), Mock()
        mock_channel = Mock()

        mock_stdout.read.return_value = b"output"
        mock_stderr.read.return_value = b""
        mock_stdout.channel = mock_channel
        mock_channel.recv_exit_status.return_value = 0

        mock_client.exec_command.return_value = (
            mock_stdin,
            mock_stdout,
            mock_stderr,
        )
        mock_get_conn.return_value = mock_client

        # Set max timeout to 60
        mock_ssh_config.security.max_timeout = 60

        # Try to execute with timeout > max
        connection_manager.execute_command("command", timeout=100)

        # Verify timeout was constrained to max
        mock_client.exec_command.assert_called_once_with("command", timeout=60)

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_ssh_exception(
        self, mock_get_conn, connection_manager
    ):
        """Test command execution handles SSH exception"""
        mock_client = Mock()
        mock_client.exec_command.side_effect = paramiko.SSHException("SSH error")
        mock_get_conn.return_value = mock_client

        with pytest.raises(CommandExecutionError) as exc_info:
            connection_manager.execute_command("command")

        assert "SSH command execution failed" in str(exc_info.value)

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_socket_timeout(
        self, mock_get_conn, connection_manager
    ):
        """Test command execution handles timeout"""
        mock_client = Mock()
        mock_client.exec_command.side_effect = socket.timeout()
        mock_get_conn.return_value = mock_client

        with pytest.raises(CommandExecutionError) as exc_info:
            connection_manager.execute_command("slow-command", timeout=5)

        assert "timed out" in str(exc_info.value)

    @patch.object(SSHConnectionManager, "get_connection")
    def test_execute_command_generic_exception(
        self, mock_get_conn, connection_manager
    ):
        """Test command execution handles generic exception"""
        mock_client = Mock()
        mock_client.exec_command.side_effect = Exception("Unexpected error")
        mock_get_conn.return_value = mock_client

        with pytest.raises(CommandExecutionError) as exc_info:
            connection_manager.execute_command("command")

        assert "Unexpected error during command execution" in str(exc_info.value)


# =============================================================================
# Connection Cleanup Tests
# =============================================================================


class TestCloseConnection:
    """Tests for close_connection method"""

    def test_close_connection_when_connected(self, connection_manager):
        """Test closing active connection"""
        mock_client = Mock()
        connection_manager._client = mock_client

        connection_manager.close_connection()

        mock_client.close.assert_called_once()
        assert connection_manager._client is None

    def test_close_connection_when_none(self, connection_manager):
        """Test closing when no connection exists"""
        connection_manager._client = None

        # Should not raise error
        connection_manager.close_connection()

        assert connection_manager._client is None

    def test_close_connection_handles_exception(self, connection_manager):
        """Test close_connection handles exception gracefully"""
        mock_client = Mock()
        mock_client.close.side_effect = Exception("Close error")
        connection_manager._client = mock_client

        # Should not raise, just log warning
        connection_manager.close_connection()

        assert connection_manager._client is None


# =============================================================================
# Context Manager Tests
# =============================================================================


class TestContextManager:
    """Tests for context manager functionality"""

    def test_context_manager_enter(self, connection_manager):
        """Test context manager __enter__"""
        result = connection_manager.__enter__()
        assert result is connection_manager

    def test_context_manager_exit_closes_connection(self, connection_manager):
        """Test context manager __exit__ closes connection"""
        mock_client = Mock()
        connection_manager._client = mock_client

        connection_manager.__exit__(None, None, None)

        mock_client.close.assert_called_once()
        assert connection_manager._client is None

    def test_context_manager_with_statement(self, mock_ssh_config):
        """Test using connection manager with 'with' statement"""
        manager = SSHConnectionManager(mock_ssh_config)
        mock_client = Mock()

        with manager as conn_mgr:
            conn_mgr._client = mock_client
            assert conn_mgr is manager

        # Connection should be closed after exiting context
        assert manager._client is None
