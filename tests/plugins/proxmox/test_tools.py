"""Tests for Proxmox Plugin Tools

Tests all Proxmox plugin tools to ensure:
- Input validation works correctly
- Proxmox service is called with proper parameters
- Error handling works as expected
- Tool functions integrate properly with the Proxmox service
"""

import pytest
from unittest.mock import MagicMock
from fastmcp import FastMCP

from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.proxmox.service import ProxmoxService
from mcp_remote_exec.plugins.proxmox.tools import (
    register_proxmox_tools,
    register_proxmox_file_tools,
)


@pytest.fixture
def mock_container():
    """Create a mock ServiceContainer with Proxmox service"""
    container = MagicMock(spec=ServiceContainer)

    # Mock Proxmox service
    proxmox_service = MagicMock(spec=ProxmoxService)
    proxmox_service.exec_in_container = MagicMock(return_value="Command output")
    proxmox_service.list_containers = MagicMock(return_value="Container list")
    proxmox_service.get_container_status = MagicMock(return_value="Status: running")
    proxmox_service.start_container = MagicMock(return_value='{"success": true}')
    proxmox_service.stop_container = MagicMock(return_value='{"success": true}')
    proxmox_service.download_file_from_container = MagicMock(return_value="Download successful")
    proxmox_service.upload_file_to_container = MagicMock(return_value="Upload successful")

    container.plugin_services = {"proxmox": proxmox_service}

    # Mock output formatter
    container.output_formatter = MagicMock()
    def mock_format_error(message):
        result = MagicMock()
        result.content = message
        return result
    container.output_formatter.format_error_result = MagicMock(side_effect=mock_format_error)

    return container


@pytest.fixture
def tool_functions():
    """Dictionary to store registered tool functions"""
    return {}


@pytest.fixture
def mock_mcp(tool_functions):
    """Create a mock FastMCP server that captures tool registrations"""
    mcp = MagicMock(spec=FastMCP)

    def mock_tool(name):
        def decorator(func):
            tool_functions[name] = func
            return func
        return decorator

    mcp.tool = mock_tool
    return mcp


class TestRegisterProxmoxTools:
    """Tests for register_proxmox_tools function"""

    def test_register_proxmox_tools_registers_all_management_tools(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test that register_proxmox_tools registers all 5 container management tools"""
        register_proxmox_tools(mock_mcp, mock_container)

        # Verify all 5 management tools were registered
        assert "proxmox_container_exec_command" in tool_functions
        assert "proxmox_list_containers" in tool_functions
        assert "proxmox_container_status" in tool_functions
        assert "proxmox_start_container" in tool_functions
        assert "proxmox_stop_container" in tool_functions

    def test_register_proxmox_tools_with_missing_service(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test that register_proxmox_tools handles missing Proxmox service gracefully"""
        # Remove Proxmox service from container
        mock_container.plugin_services = {}

        register_proxmox_tools(mock_mcp, mock_container)

        # No tools should be registered
        assert len(tool_functions) == 0


class TestProxmoxContainerExecCommand:
    """Tests for proxmox_container_exec_command tool"""

    @pytest.mark.asyncio
    async def test_exec_command_with_valid_input(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_container_exec_command with valid input"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.exec_in_container.return_value = "Success output"

        tool = tool_functions["proxmox_container_exec_command"]
        result = await tool(ctid=100, command="ls -la", timeout=30, response_format="text")

        # Verify service was called correctly
        proxmox_service.exec_in_container.assert_called_once_with(
            ctid=100,
            command="ls -la",
            timeout=30,
            response_format="text"
        )
        assert result == "Success output"

    @pytest.mark.asyncio
    async def test_exec_command_with_json_format(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_container_exec_command with json response format"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]

        tool = tool_functions["proxmox_container_exec_command"]
        result = await tool(ctid=101, command="whoami", timeout=10, response_format="json")

        proxmox_service.exec_in_container.assert_called_once_with(
            ctid=101,
            command="whoami",
            timeout=10,
            response_format="json"
        )

    @pytest.mark.asyncio
    async def test_exec_command_with_empty_command(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_container_exec_command with empty command returns validation error"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]

        tool = tool_functions["proxmox_container_exec_command"]
        result = await tool(ctid=100, command="", timeout=30, response_format="text")

        # Should return error, not call service
        proxmox_service.exec_in_container.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    async def test_exec_command_handles_service_exception(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_container_exec_command handles service exceptions"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.exec_in_container.side_effect = Exception("Container not found")

        tool = tool_functions["proxmox_container_exec_command"]
        result = await tool(ctid=100, command="ls", timeout=30, response_format="text")

        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()


class TestProxmoxListContainers:
    """Tests for proxmox_list_containers tool"""

    @pytest.mark.asyncio
    async def test_list_containers_with_text_format(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_list_containers with text format"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.list_containers.return_value = "Container list"

        tool = tool_functions["proxmox_list_containers"]
        result = await tool(response_format="text")

        proxmox_service.list_containers.assert_called_once_with(response_format="text")
        assert result == "Container list"

    @pytest.mark.asyncio
    async def test_list_containers_with_json_format(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_list_containers with json format"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]

        tool = tool_functions["proxmox_list_containers"]
        result = await tool(response_format="json")

        proxmox_service.list_containers.assert_called_once_with(response_format="json")


class TestProxmoxContainerStatus:
    """Tests for proxmox_container_status tool"""

    @pytest.mark.asyncio
    async def test_container_status_with_valid_ctid(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_container_status with valid container ID"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.get_container_status.return_value = "Status: running"

        tool = tool_functions["proxmox_container_status"]
        result = await tool(ctid=100, response_format="text")

        proxmox_service.get_container_status.assert_called_once_with(
            ctid=100, response_format="text"
        )
        assert result == "Status: running"


class TestProxmoxStartContainer:
    """Tests for proxmox_start_container tool"""

    @pytest.mark.asyncio
    async def test_start_container_with_valid_ctid(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_start_container with valid container ID"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.start_container.return_value = '{"success": true}'

        tool = tool_functions["proxmox_start_container"]
        result = await tool(ctid=100)

        proxmox_service.start_container.assert_called_once_with(ctid=100)
        assert result == '{"success": true}'

    @pytest.mark.asyncio
    async def test_start_container_with_invalid_ctid(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_start_container with invalid container ID"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]

        tool = tool_functions["proxmox_start_container"]
        result = await tool(ctid=99)  # Below minimum of 100

        # Should return validation error
        proxmox_service.start_container.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()


class TestProxmoxStopContainer:
    """Tests for proxmox_stop_container tool"""

    @pytest.mark.asyncio
    async def test_stop_container_with_valid_ctid(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_stop_container with valid container ID"""
        register_proxmox_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.stop_container.return_value = '{"success": true}'

        tool = tool_functions["proxmox_stop_container"]
        result = await tool(ctid=100)

        proxmox_service.stop_container.assert_called_once_with(ctid=100)
        assert result == '{"success": true}'


class TestRegisterProxmoxFileTools:
    """Tests for register_proxmox_file_tools function"""

    def test_register_proxmox_file_tools_registers_both_tools(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test that register_proxmox_file_tools registers both file transfer tools"""
        register_proxmox_file_tools(mock_mcp, mock_container)

        # Verify both file transfer tools were registered
        assert "proxmox_download_file_from_container" in tool_functions
        assert "proxmox_upload_file_to_container" in tool_functions


class TestProxmoxDownloadFile:
    """Tests for proxmox_download_file_from_container tool"""

    @pytest.mark.asyncio
    async def test_download_file_with_valid_input(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_download_file_from_container with valid input"""
        register_proxmox_file_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.download_file_from_container.return_value = "Download successful"

        tool = tool_functions["proxmox_download_file_from_container"]
        result = await tool(
            ctid=100,
            container_path="/etc/nginx/nginx.conf",
            local_path="./nginx.conf",
            overwrite=False
        )

        proxmox_service.download_file_from_container.assert_called_once_with(
            ctid=100,
            container_path="/etc/nginx/nginx.conf",
            local_path="./nginx.conf",
            overwrite=False
        )
        assert result == "Download successful"

    @pytest.mark.asyncio
    async def test_download_file_with_empty_paths(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_download_file_from_container with empty paths"""
        register_proxmox_file_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]

        tool = tool_functions["proxmox_download_file_from_container"]
        result = await tool(
            ctid=100,
            container_path="",
            local_path="",
            overwrite=False
        )

        # Should return validation error
        proxmox_service.download_file_from_container.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()


class TestProxmoxUploadFile:
    """Tests for proxmox_upload_file_to_container tool"""

    @pytest.mark.asyncio
    async def test_upload_file_with_valid_input(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_upload_file_to_container with valid input"""
        register_proxmox_file_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.upload_file_to_container.return_value = "Upload successful"

        tool = tool_functions["proxmox_upload_file_to_container"]
        result = await tool(
            ctid=100,
            local_path="./config.yaml",
            container_path="/etc/app/config.yaml",
            permissions=644,
            overwrite=True
        )

        proxmox_service.upload_file_to_container.assert_called_once_with(
            ctid=100,
            local_path="./config.yaml",
            container_path="/etc/app/config.yaml",
            permissions=644,
            overwrite=True
        )
        assert result == "Upload successful"

    @pytest.mark.asyncio
    async def test_upload_file_handles_service_exception(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test proxmox_upload_file_to_container handles service exceptions"""
        register_proxmox_file_tools(mock_mcp, mock_container)
        proxmox_service = mock_container.plugin_services["proxmox"]
        proxmox_service.upload_file_to_container.side_effect = Exception("File not found")

        tool = tool_functions["proxmox_upload_file_to_container"]
        result = await tool(
            ctid=100,
            local_path="./missing.txt",
            container_path="/tmp/file.txt",
            permissions=None,
            overwrite=False
        )

        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()
