"""Tests for Core MCP Tools

Tests the ssh_exec_command tool and file transfer tools to ensure:
- Input validation works correctly
- Services are called with proper parameters
- Error handling works as expected
- Tool functions integrate properly with services
"""

import pytest
from unittest.mock import MagicMock, patch

# Patch bootstrap.initialize before importing mcp_tools to prevent module-level initialization
with patch("mcp_remote_exec.presentation.bootstrap.initialize"):
    from mcp_remote_exec.presentation import mcp_tools

from mcp_remote_exec.presentation.service_container import ServiceContainer


@pytest.fixture
def mock_container():
    """Create a mock ServiceContainer with all required services"""
    container = MagicMock(spec=ServiceContainer)

    # Mock command service
    container.command_service = MagicMock()
    container.command_service.execute_command = MagicMock(return_value="Command output")

    # Mock file service
    container.file_service = MagicMock()
    container.file_service.upload_file = MagicMock(return_value="Upload successful")
    container.file_service.download_file = MagicMock(return_value="Download successful")

    # Mock output formatter
    container.output_formatter = MagicMock()
    def mock_format_error(message):
        result = MagicMock()
        result.content = message
        return result
    container.output_formatter.format_error_result = MagicMock(side_effect=mock_format_error)

    return container


class TestSSHExecCommand:
    """Tests for ssh_exec_command tool"""

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_with_valid_input(self, mock_get_container, mock_container):
        """Test ssh_exec_command with valid input calls command service correctly"""
        mock_get_container.return_value = mock_container
        mock_container.command_service.execute_command.return_value = "Success output"

        # Get the actual function from the wrapped tool
        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="ls -la",
            timeout=30,
            response_format="text"
        )

        # Verify service was called with correct parameters
        mock_container.command_service.execute_command.assert_called_once_with(
            command="ls -la",
            timeout=30,
            response_format="text"
        )
        assert result == "Success output"

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_with_json_format(self, mock_get_container, mock_container):
        """Test ssh_exec_command with json response format"""
        mock_get_container.return_value = mock_container
        mock_container.command_service.execute_command.return_value = '{"status": "ok"}'

        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="whoami",
            timeout=10,
            response_format="json"
        )

        mock_container.command_service.execute_command.assert_called_once_with(
            command="whoami",
            timeout=10,
            response_format="json"
        )
        assert result == '{"status": "ok"}'

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_with_empty_command(self, mock_get_container, mock_container):
        """Test ssh_exec_command with empty command returns validation error"""
        mock_get_container.return_value = mock_container

        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="",
            timeout=30,
            response_format="text"
        )

        # Should return error, not call service
        mock_container.command_service.execute_command.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_with_invalid_timeout(self, mock_get_container, mock_container):
        """Test ssh_exec_command with invalid timeout returns validation error"""
        mock_get_container.return_value = mock_container

        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="ls",
            timeout=500,  # Exceeds MAX_TIMEOUT of 300
            response_format="text"
        )

        # Should return error, not call service
        mock_container.command_service.execute_command.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_with_invalid_response_format(self, mock_get_container, mock_container):
        """Test ssh_exec_command with invalid response format returns validation error"""
        mock_get_container.return_value = mock_container

        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="ls",
            timeout=30,
            response_format="xml"  # Invalid format
        )

        # Should return error, not call service
        mock_container.command_service.execute_command.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.mcp_tools.bootstrap.get_container")
    async def test_ssh_exec_command_handles_service_exception(self, mock_get_container, mock_container):
        """Test ssh_exec_command handles exceptions from command service"""
        mock_get_container.return_value = mock_container
        mock_container.command_service.execute_command.side_effect = Exception("SSH connection failed")

        tool_func = mcp_tools.ssh_exec_command.fn
        result = await tool_func(
            command="ls",
            timeout=30,
            response_format="text"
        )

        # Should format error result
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()


class TestSSHFileTransferTools:
    """Tests for SSH file transfer tools (upload/download)"""

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.bootstrap.get_container")
    async def test_ssh_upload_file_with_valid_input(self, mock_get_container, mock_container):
        """Test ssh_upload_file with valid input calls file service correctly"""
        from mcp_remote_exec.presentation.bootstrap import _register_ssh_file_transfer_tools
        from fastmcp import FastMCP

        mock_get_container.return_value = mock_container
        mock_container.file_service.upload_file.return_value = "Upload successful"

        # Create a mock MCP server and register tools
        mcp = MagicMock(spec=FastMCP)
        tool_functions = {}

        # Capture tool registration
        def mock_tool(name):
            def decorator(func):
                tool_functions[name] = func
                return func
            return decorator

        mcp.tool = mock_tool

        # Register the tools
        _register_ssh_file_transfer_tools(mcp)

        # Call the registered upload tool
        upload_tool = tool_functions["ssh_upload_file"]
        result = await upload_tool(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            permissions=644,
            overwrite=False
        )

        # Verify service was called
        mock_container.file_service.upload_file.assert_called_once_with(
            local_path="/tmp/test.txt",
            remote_path="/data/test.txt",
            permissions=644,
            overwrite=False
        )
        assert result == "Upload successful"

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.bootstrap.get_container")
    async def test_ssh_upload_file_with_empty_paths(self, mock_get_container, mock_container):
        """Test ssh_upload_file with empty paths returns validation error"""
        from mcp_remote_exec.presentation.bootstrap import _register_ssh_file_transfer_tools
        from fastmcp import FastMCP

        mock_get_container.return_value = mock_container

        # Create mock MCP and register tools
        mcp = MagicMock(spec=FastMCP)
        tool_functions = {}

        def mock_tool(name):
            def decorator(func):
                tool_functions[name] = func
                return func
            return decorator

        mcp.tool = mock_tool
        _register_ssh_file_transfer_tools(mcp)

        # Call with empty paths
        upload_tool = tool_functions["ssh_upload_file"]
        result = await upload_tool(
            local_path="",
            remote_path="",
            permissions=None,
            overwrite=False
        )

        # Should return error, not call service
        mock_container.file_service.upload_file.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.bootstrap.get_container")
    async def test_ssh_download_file_with_valid_input(self, mock_get_container, mock_container):
        """Test ssh_download_file with valid input calls file service correctly"""
        from mcp_remote_exec.presentation.bootstrap import _register_ssh_file_transfer_tools
        from fastmcp import FastMCP

        mock_get_container.return_value = mock_container
        mock_container.file_service.download_file.return_value = "Download successful"

        # Create mock MCP and register tools
        mcp = MagicMock(spec=FastMCP)
        tool_functions = {}

        def mock_tool(name):
            def decorator(func):
                tool_functions[name] = func
                return func
            return decorator

        mcp.tool = mock_tool
        _register_ssh_file_transfer_tools(mcp)

        # Call the download tool
        download_tool = tool_functions["ssh_download_file"]
        result = await download_tool(
            remote_path="/data/test.txt",
            local_path="/tmp/test.txt",
            overwrite=True
        )

        # Verify service was called
        mock_container.file_service.download_file.assert_called_once_with(
            remote_path="/data/test.txt",
            local_path="/tmp/test.txt",
            overwrite=True
        )
        assert result == "Download successful"

    @pytest.mark.asyncio
    @patch("mcp_remote_exec.presentation.bootstrap.get_container")
    async def test_ssh_download_file_handles_service_exception(self, mock_get_container, mock_container):
        """Test ssh_download_file handles exceptions from file service"""
        from mcp_remote_exec.presentation.bootstrap import _register_ssh_file_transfer_tools
        from fastmcp import FastMCP

        mock_get_container.return_value = mock_container
        mock_container.file_service.download_file.side_effect = Exception("File not found")

        # Create mock MCP and register tools
        mcp = MagicMock(spec=FastMCP)
        tool_functions = {}

        def mock_tool(name):
            def decorator(func):
                tool_functions[name] = func
                return func
            return decorator

        mcp.tool = mock_tool
        _register_ssh_file_transfer_tools(mcp)

        # Call the download tool
        download_tool = tool_functions["ssh_download_file"]
        result = await download_tool(
            remote_path="/data/test.txt",
            local_path="/tmp/test.txt",
            overwrite=False
        )

        # Should format error result
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()
