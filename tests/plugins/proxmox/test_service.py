"""Tests for Proxmox Plugin Service"""

import json
import pytest
from unittest.mock import MagicMock, patch

from mcp_remote_exec.plugins.proxmox.service import ProxmoxService
from mcp_remote_exec.data_access.ssh_connection_manager import ExecutionResult


@pytest.fixture
def mock_command_service():
    """Create a mock CommandService"""
    return MagicMock()


@pytest.fixture
def mock_file_service():
    """Create a mock FileTransferService"""
    return MagicMock()


@pytest.fixture
def proxmox_service(mock_command_service, mock_file_service):
    """Create a ProxmoxService instance with mocks"""
    return ProxmoxService(
        command_service=mock_command_service,
        file_service=mock_file_service,
    )


class TestProxmoxServiceInitialization:
    """Tests for ProxmoxService initialization"""

    def test_service_initialization(self, proxmox_service):
        """Test that ProxmoxService initializes correctly"""
        assert proxmox_service is not None
        assert proxmox_service.command_service is not None
        assert proxmox_service.file_service is not None


class TestExecInContainer:
    """Tests for exec_in_container method"""

    def test_exec_in_container_success(self, proxmox_service, mock_command_service):
        """Test successful command execution in container"""
        mock_command_service.execute_command.return_value = "Command output"

        result = proxmox_service.exec_in_container(
            ctid=100,
            command="echo test",
            timeout=30,
            response_format="text",
        )

        assert result == "Command output"
        mock_command_service.execute_command.assert_called_once()
        call_args = mock_command_service.execute_command.call_args
        assert "pct exec 100" in call_args[0][0]
        assert "echo test" in call_args[0][0]

    def test_exec_in_container_with_quotes(self, proxmox_service, mock_command_service):
        """Test command with single quotes is properly escaped"""
        mock_command_service.execute_command.return_value = "Output"

        proxmox_service.exec_in_container(
            ctid=100,
            command="echo 'hello world'",
            timeout=30,
            response_format="text",
        )

        call_args = mock_command_service.execute_command.call_args
        # Verify quotes are escaped
        assert "'\\''" in call_args[0][0]

    def test_exec_in_container_not_found(self, proxmox_service, mock_command_service):
        """Test handling when container does not exist"""
        mock_command_service.execute_command.side_effect = Exception(
            "Container does not exist"
        )

        result = proxmox_service.exec_in_container(
            ctid=999,
            command="echo test",
            timeout=30,
            response_format="text",
        )

        assert "not found" in result.lower()
        assert "999" in result


class TestListContainers:
    """Tests for list_containers method"""

    def test_list_containers_text_format(self, proxmox_service, mock_command_service):
        """Test list_containers with text format"""
        # Mock pct list output
        mock_result = ExecutionResult(
            exit_code=0,
            stdout="VMID       Status     Lock         Name\n100        running                 web-server\n101        stopped                 db-server",
            stderr="",
            timeout_reached=False,
            command="pct list",
        )
        mock_command_service.execute_command_raw.return_value = mock_result

        result = proxmox_service.list_containers(response_format="text")

        assert isinstance(result, str)
        assert "100" in result
        assert "101" in result
        assert "web-server" in result or "CTID" in result  # Either data or header

    def test_list_containers_json_format(self, proxmox_service, mock_command_service):
        """Test list_containers with JSON format"""
        mock_result = ExecutionResult(
            exit_code=0,
            stdout="VMID       Status     Lock         Name\n100        running                 web-server\n101        stopped                 db-server",
            stderr="",
            timeout_reached=False,
            command="pct list",
        )
        mock_command_service.execute_command_raw.return_value = mock_result

        result = proxmox_service.list_containers(response_format="json")

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_list_containers_empty(self, proxmox_service, mock_command_service):
        """Test list_containers when no containers exist"""
        mock_result = ExecutionResult(
            exit_code=0,
            stdout="VMID       Status     Lock         Name",
            stderr="",
            timeout_reached=False,
            command="pct list",
        )
        mock_command_service.execute_command_raw.return_value = mock_result

        result = proxmox_service.list_containers(response_format="text")

        assert "No containers found" in result or "CTID" in result


class TestContainerStatus:
    """Tests for get_container_status method"""

    def test_get_container_status_running(self, proxmox_service, mock_command_service):
        """Test getting status of running container"""
        mock_result = ExecutionResult(
            exit_code=0,
            stdout="running",
            stderr="",
            timeout_reached=False,
            command="pct status 100",
        )
        mock_command_service.execute_command_raw.return_value = mock_result

        result = proxmox_service.get_container_status(
            ctid=100, response_format="text"
        )

        assert "running" in result.lower()

    def test_get_container_status_stopped(self, proxmox_service, mock_command_service):
        """Test getting status of stopped container"""
        mock_result = ExecutionResult(
            exit_code=0,
            stdout="stopped",
            stderr="",
            timeout_reached=False,
            command="pct status 100",
        )
        mock_command_service.execute_command_raw.return_value = mock_result

        result = proxmox_service.get_container_status(
            ctid=100, response_format="text"
        )

        assert "stopped" in result.lower()


class TestContainerActions:
    """Tests for start_container and stop_container methods"""

    def test_start_container_success(self, proxmox_service, mock_command_service):
        """Test starting a stopped container"""
        mock_command_service.execute_command.return_value = "Container started"

        result = proxmox_service.start_container(ctid=100)

        # Should return JSON with success
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["ctid"] == 100
        mock_command_service.execute_command.assert_called_once()

    def test_stop_container_success(self, proxmox_service, mock_command_service):
        """Test stopping a running container"""
        mock_command_service.execute_command.return_value = "Container stopped"

        result = proxmox_service.stop_container(ctid=100)

        # Should return JSON with success
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["ctid"] == 100
        mock_command_service.execute_command.assert_called_once()
