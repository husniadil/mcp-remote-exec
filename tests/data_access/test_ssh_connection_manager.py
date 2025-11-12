"""
Tests for SSHConnectionManager

Basic smoke tests for SSH connection manager functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from mcp_remote_exec.data_access.ssh_connection_manager import (
    SSHConnectionManager,
    ExecutionResult,
)
from mcp_remote_exec.data_access.exceptions import (
    SSHConnectionError,
    AuthenticationError,
)


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


def test_connection_manager_initialization(connection_manager, mock_ssh_config):
    """Test that SSHConnectionManager initializes correctly"""
    assert connection_manager is not None
    assert connection_manager.config == mock_ssh_config


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
