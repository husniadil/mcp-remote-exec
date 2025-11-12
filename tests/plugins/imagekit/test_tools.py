"""Tests for ImageKit Plugin Tools

Tests all ImageKit plugin tools to ensure:
- Input validation works correctly
- ImageKit service is called with proper parameters
- Error handling works as expected
- Tool functions integrate properly with the ImageKit service
"""

import pytest
from unittest.mock import MagicMock
from fastmcp import FastMCP

from mcp_remote_exec.presentation.service_container import ServiceContainer
from mcp_remote_exec.plugins.imagekit.service import ImageKitService
from mcp_remote_exec.plugins.imagekit.tools import register_imagekit_tools


@pytest.fixture
def mock_container():
    """Create a mock ServiceContainer with ImageKit service"""
    container = MagicMock(spec=ServiceContainer)

    # Mock ImageKit service
    imagekit_service = MagicMock(spec=ImageKitService)
    imagekit_service.request_upload = MagicMock(
        return_value='{"transfer_id": "test-123", "upload_command": "curl ..."}'
    )
    imagekit_service.confirm_upload = MagicMock(return_value='{"success": true}')
    imagekit_service.request_download = MagicMock(
        return_value='{"transfer_id": "test-456", "download_url": "https://..."}'
    )
    imagekit_service.confirm_download = MagicMock(return_value='{"success": true}')

    container.plugin_services = {"imagekit": imagekit_service}

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


class TestRegisterImageKitTools:
    """Tests for register_imagekit_tools function"""

    def test_register_imagekit_tools_registers_all_tools(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test that register_imagekit_tools registers all 4 file transfer tools"""
        register_imagekit_tools(mock_mcp, mock_container)

        # Verify all 4 tools were registered
        assert "imagekit_request_upload" in tool_functions
        assert "imagekit_confirm_upload" in tool_functions
        assert "imagekit_request_download" in tool_functions
        assert "imagekit_confirm_download" in tool_functions

    def test_register_imagekit_tools_with_missing_service(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test that register_imagekit_tools handles missing ImageKit service gracefully"""
        # Remove ImageKit service from container
        mock_container.plugin_services = {}

        register_imagekit_tools(mock_mcp, mock_container)

        # No tools should be registered
        assert len(tool_functions) == 0


class TestImageKitRequestUpload:
    """Tests for imagekit_request_upload tool"""

    @pytest.mark.asyncio
    async def test_request_upload_to_host(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_upload for host upload"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.request_upload.return_value = '{"transfer_id": "test-123"}'

        tool = tool_functions["imagekit_request_upload"]
        result = await tool(
            remote_path="/tmp/file.txt",
            permissions=644,
            overwrite=False,
            ctid=None
        )

        # Verify service was called correctly
        imagekit_service.request_upload.assert_called_once_with(
            remote_path="/tmp/file.txt",
            permissions=644,
            overwrite=False,
            ctid=None
        )
        assert "test-123" in result

    @pytest.mark.asyncio
    async def test_request_upload_to_container(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_upload for container upload"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_request_upload"]
        result = await tool(
            remote_path="/app/config.txt",
            permissions=755,
            overwrite=True,
            ctid=100
        )

        imagekit_service.request_upload.assert_called_once_with(
            remote_path="/app/config.txt",
            permissions=755,
            overwrite=True,
            ctid=100
        )

    @pytest.mark.asyncio
    async def test_request_upload_with_empty_path(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_upload with empty remote path"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_request_upload"]
        result = await tool(
            remote_path="",
            permissions=None,
            overwrite=False,
            ctid=None
        )

        # Should return validation error
        imagekit_service.request_upload.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    async def test_request_upload_handles_service_exception(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_upload handles service exceptions"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.request_upload.side_effect = Exception("ImageKit API error")

        tool = tool_functions["imagekit_request_upload"]
        result = await tool(
            remote_path="/tmp/file.txt",
            permissions=644,
            overwrite=False,
            ctid=None
        )

        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()


class TestImageKitConfirmUpload:
    """Tests for imagekit_confirm_upload tool"""

    @pytest.mark.asyncio
    async def test_confirm_upload_without_file_id(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_upload without file_id"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.confirm_upload.return_value = '{"success": true}'

        tool = tool_functions["imagekit_confirm_upload"]
        result = await tool(transfer_id="test-123", file_id=None)

        imagekit_service.confirm_upload.assert_called_once_with(
            transfer_id="test-123",
            file_id=None
        )
        assert "success" in result

    @pytest.mark.asyncio
    async def test_confirm_upload_with_file_id(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_upload with file_id (recommended)"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_confirm_upload"]
        result = await tool(
            transfer_id="test-123",
            file_id="690b82f45c7cd75eb8328078"
        )

        imagekit_service.confirm_upload.assert_called_once_with(
            transfer_id="test-123",
            file_id="690b82f45c7cd75eb8328078"
        )

    @pytest.mark.asyncio
    async def test_confirm_upload_with_empty_transfer_id(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_upload with empty transfer_id"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_confirm_upload"]
        result = await tool(transfer_id="", file_id=None)

        # Should return validation error
        imagekit_service.confirm_upload.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()


class TestImageKitRequestDownload:
    """Tests for imagekit_request_download tool"""

    @pytest.mark.asyncio
    async def test_request_download_from_host(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_download from host"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.request_download.return_value = '{"transfer_id": "test-456"}'

        tool = tool_functions["imagekit_request_download"]
        result = await tool(remote_path="/data/app.conf", ctid=None)

        imagekit_service.request_download.assert_called_once_with(
            remote_path="/data/app.conf",
            ctid=None
        )
        assert "test-456" in result

    @pytest.mark.asyncio
    async def test_request_download_from_container(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_download from container"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_request_download"]
        result = await tool(remote_path="/app/logs/app.log", ctid=100)

        imagekit_service.request_download.assert_called_once_with(
            remote_path="/app/logs/app.log",
            ctid=100
        )

    @pytest.mark.asyncio
    async def test_request_download_with_empty_path(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_download with empty remote path"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_request_download"]
        result = await tool(remote_path="", ctid=None)

        # Should return validation error
        imagekit_service.request_download.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    async def test_request_download_handles_service_exception(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_request_download handles service exceptions"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.request_download.side_effect = Exception("File not found")

        tool = tool_functions["imagekit_request_download"]
        result = await tool(remote_path="/data/missing.txt", ctid=None)

        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()


class TestImageKitConfirmDownload:
    """Tests for imagekit_confirm_download tool"""

    @pytest.mark.asyncio
    async def test_confirm_download_with_valid_transfer_id(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_download with valid transfer_id"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.confirm_download.return_value = '{"success": true}'

        tool = tool_functions["imagekit_confirm_download"]
        result = await tool(transfer_id="test-456")

        imagekit_service.confirm_download.assert_called_once_with(transfer_id="test-456")
        assert "success" in result

    @pytest.mark.asyncio
    async def test_confirm_download_with_empty_transfer_id(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_download with empty transfer_id"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]

        tool = tool_functions["imagekit_confirm_download"]
        result = await tool(transfer_id="")

        # Should return validation error
        imagekit_service.confirm_download.assert_not_called()
        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "validation error" in result.lower()

    @pytest.mark.asyncio
    async def test_confirm_download_handles_service_exception(
        self, mock_mcp, mock_container, tool_functions
    ):
        """Test imagekit_confirm_download handles service exceptions"""
        register_imagekit_tools(mock_mcp, mock_container)
        imagekit_service = mock_container.plugin_services["imagekit"]
        imagekit_service.confirm_download.side_effect = Exception("Transfer not found")

        tool = tool_functions["imagekit_confirm_download"]
        result = await tool(transfer_id="invalid-id")

        mock_container.output_formatter.format_error_result.assert_called_once()
        assert "error" in result.lower()
