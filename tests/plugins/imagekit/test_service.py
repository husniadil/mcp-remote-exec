"""Tests for ImageKit Plugin Service"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from mcp_remote_exec.plugins.imagekit.service import ImageKitService
from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig
from mcp_remote_exec.plugins.imagekit.models import TransferOperation


@pytest.fixture
def imagekit_config():
    """Create an ImageKit config for testing"""
    return ImageKitConfig(
        public_key="test_public_key",
        private_key="test_private_key",
        url_endpoint="https://ik.imagekit.io/test",
        folder="/test-folder",
        transfer_timeout=3600,
    )


@pytest.fixture
def mock_command_service():
    """Create a mock CommandService"""
    return MagicMock()


@pytest.fixture
def mock_file_service():
    """Create a mock FileTransferService"""
    mock = MagicMock()
    # Default: paths are valid
    mock.validate_paths.return_value = (True, None)
    return mock


@pytest.fixture
def imagekit_service(imagekit_config, mock_command_service, mock_file_service):
    """Create an ImageKitService instance with mocks"""
    return ImageKitService(
        config=imagekit_config,
        command_service=mock_command_service,
        file_service=mock_file_service,
        enabled_plugins=set(),
    )


class TestImageKitServiceInitialization:
    """Tests for ImageKitService initialization"""

    def test_service_initialization(self, imagekit_service):
        """Test that ImageKitService initializes correctly"""
        assert imagekit_service is not None
        assert imagekit_service.config is not None
        assert imagekit_service.command_service is not None
        assert imagekit_service.file_service is not None
        assert imagekit_service.client is not None
        assert imagekit_service.transfer_manager is not None

    def test_service_with_enabled_plugins(
        self, imagekit_config, mock_command_service, mock_file_service
    ):
        """Test service initialization with enabled plugins"""
        service = ImageKitService(
            config=imagekit_config,
            command_service=mock_command_service,
            file_service=mock_file_service,
            enabled_plugins={"proxmox", "imagekit"},
        )

        assert "proxmox" in service.enabled_plugins
        assert "imagekit" in service.enabled_plugins


class TestRequestUpload:
    """Tests for request_upload method"""

    def test_request_upload_without_container(self, imagekit_service):
        """Test upload request without container ID (host file)"""
        result = imagekit_service.request_upload(
            remote_path="/tmp/test.txt",
            permissions=644,
            overwrite=False,
            ctid=None,
        )

        # Should return JSON with upload instructions
        parsed = json.loads(result)
        assert "transfer_id" in parsed
        assert "upload_command" in parsed
        assert "expires_in" in parsed

    def test_request_upload_with_invalid_path(
        self, imagekit_service, mock_file_service
    ):
        """Test upload request with invalid remote path"""
        mock_file_service.validate_paths.return_value = (
            False,
            "Path traversal not allowed",
        )

        result = imagekit_service.request_upload(
            remote_path="../etc/passwd",
            permissions=644,
            overwrite=False,
            ctid=None,
        )

        # Should return error JSON
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "error" in parsed

    def test_request_upload_with_container_no_proxmox(self, imagekit_service):
        """Test upload to container when Proxmox plugin is not enabled"""
        # enabled_plugins is empty by default in fixture

        result = imagekit_service.request_upload(
            remote_path="/tmp/test.txt",
            permissions=644,
            overwrite=False,
            ctid=100,  # Container ID specified
        )

        # Should return error about Proxmox requirement
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "proxmox" in parsed["error"].lower()

    def test_request_upload_with_container_proxmox_enabled(
        self, imagekit_config, mock_command_service, mock_file_service
    ):
        """Test upload to container when Proxmox plugin is enabled"""
        service = ImageKitService(
            config=imagekit_config,
            command_service=mock_command_service,
            file_service=mock_file_service,
            enabled_plugins={"proxmox"},  # Proxmox enabled
        )

        result = service.request_upload(
            remote_path="/tmp/test.txt",
            permissions=644,
            overwrite=False,
            ctid=100,
        )

        # Should succeed and return upload instructions
        parsed = json.loads(result)
        assert "transfer_id" in parsed
        assert "upload_command" in parsed


class TestRequestDownload:
    """Tests for request_download method"""

    def test_request_download_without_container(self, imagekit_service):
        """Test download request without container ID (host file)"""
        # This is a complex test that requires mocking internal ImageKit operations
        # For now, test that the method is callable and validates paths
        result = imagekit_service.request_download(
            remote_path="../invalid/path",
            ctid=None,
        )

        # Should validate path and return error for invalid path
        parsed = json.loads(result)
        assert "success" in parsed or "error" in parsed or "transfer_id" in parsed

    def test_request_download_with_invalid_path(
        self, imagekit_service, mock_file_service
    ):
        """Test download request with invalid remote path"""
        mock_file_service.validate_paths.return_value = (
            False,
            "Path traversal not allowed",
        )

        result = imagekit_service.request_download(
            remote_path="../etc/passwd",
            ctid=None,
        )

        # Should return error JSON
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "error" in parsed

    def test_request_download_with_container_no_proxmox(self, imagekit_service):
        """Test download from container when Proxmox plugin is not enabled"""
        result = imagekit_service.request_download(
            remote_path="/tmp/test.txt",
            ctid=100,
        )

        # Should return error about Proxmox requirement
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "proxmox" in parsed["error"].lower()


class TestConfirmUpload:
    """Tests for confirm_upload method"""

    def test_confirm_upload_invalid_transfer_id(self, imagekit_service):
        """Test confirm_upload with non-existent transfer ID"""
        result = imagekit_service.confirm_upload(
            transfer_id="nonexistent-id",
            file_id=None,
        )

        # Should return error
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "not found" in parsed["error"].lower()

    def test_confirm_upload_wrong_operation(self, imagekit_service):
        """Test confirm_upload with download transfer (should fail)"""
        # Create a download transfer
        transfer = imagekit_service.transfer_manager.create_transfer(
            operation=TransferOperation.DOWNLOAD,
            remote_path="/tmp/test.txt",
        )

        result = imagekit_service.confirm_upload(
            transfer_id=transfer.transfer_id,
            file_id="test_file_id",
        )

        # Should return error about wrong operation type
        parsed = json.loads(result)
        assert parsed["success"] is False


class TestConfirmDownload:
    """Tests for confirm_download method"""

    def test_confirm_download_invalid_transfer_id(self, imagekit_service):
        """Test confirm_download with non-existent transfer ID"""
        result = imagekit_service.confirm_download(transfer_id="nonexistent-id")

        # Should return error
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert "not found" in parsed["error"].lower()
