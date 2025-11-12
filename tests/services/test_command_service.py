"""
Tests for CommandService

Basic smoke tests for command service functionality.
"""

import pytest
from unittest.mock import MagicMock
from mcp_remote_exec.services.command_service import CommandService
from mcp_remote_exec.data_access.ssh_connection_manager import ExecutionResult


@pytest.fixture
def mock_connection_manager():
    """Create a mock SSH connection manager"""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_ssh_config(mock_host_config, mock_security_config):
    """Create a mock SSH config"""
    mock = MagicMock()
    mock.get_host.return_value = mock_host_config
    mock.security = mock_security_config
    return mock


@pytest.fixture
def command_service(mock_connection_manager, mock_ssh_config):
    """Create a CommandService instance with mocks"""
    return CommandService(mock_connection_manager, mock_ssh_config)


def test_command_service_initialization(command_service):
    """Test that CommandService initializes correctly"""
    assert command_service is not None
    assert command_service.connection_manager is not None
    assert command_service.config is not None
    assert command_service.output_formatter is not None


def test_execute_command_raw_returns_execution_result(
    command_service, mock_connection_manager
):
    """Test that execute_command_raw returns ExecutionResult"""
    # Setup mock
    expected_result = ExecutionResult(
        exit_code=0,
        stdout="test output",
        stderr="",
        timeout_reached=False,
        command="echo test",
    )
    mock_connection_manager.execute_command.return_value = expected_result

    # Execute
    result = command_service.execute_command_raw("echo test", 30)

    # Assert
    assert result == expected_result
    assert result.exit_code == 0
    assert result.stdout == "test output"
    mock_connection_manager.execute_command.assert_called_once_with("echo test", 30)


def test_execute_command_raw_with_error_exit_code(
    command_service, mock_connection_manager
):
    """Test execute_command_raw with non-zero exit code"""
    # Setup mock
    error_result = ExecutionResult(
        exit_code=1,
        stdout="",
        stderr="command failed",
        timeout_reached=False,
        command="false",
    )
    mock_connection_manager.execute_command.return_value = error_result

    # Execute
    result = command_service.execute_command_raw("false", 30)

    # Assert
    assert result.exit_code == 1
    assert result.stderr == "command failed"


def test_execute_command_raw_with_custom_timeout(
    command_service, mock_connection_manager
):
    """Test execute_command_raw with custom timeout"""
    # Setup mock
    expected_result = ExecutionResult(
        exit_code=0, stdout="output", stderr="", timeout_reached=False, command="test"
    )
    mock_connection_manager.execute_command.return_value = expected_result

    # Execute with custom timeout
    result = command_service.execute_command_raw("test command", timeout=60)

    # Assert
    mock_connection_manager.execute_command.assert_called_once_with(
        "test command", 60
    )
    assert result == expected_result


def test_execute_command_raw_propagates_exceptions(
    command_service, mock_connection_manager
):
    """Test that execute_command_raw propagates exceptions from connection manager"""
    # Setup mock to raise exception
    from mcp_remote_exec.data_access.exceptions import CommandExecutionError

    mock_connection_manager.execute_command.side_effect = CommandExecutionError(
        "Connection failed"
    )

    # Execute and assert exception is raised
    with pytest.raises(CommandExecutionError):
        command_service.execute_command_raw("test", 30)
