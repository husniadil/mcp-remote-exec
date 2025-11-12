"""Tests for ImageKit Client"""

import pytest
from unittest.mock import MagicMock, patch

from mcp_remote_exec.plugins.imagekit.imagekit_client import ImageKitClient
from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig


@pytest.fixture
def imagekit_config():
    """Create an ImageKit config for testing"""
    return ImageKitConfig(
        public_key="test_public_key",
        private_key="test_private_key",
        url_endpoint="https://ik.imagekit.io/test",
        folder="/test-folder",
    )


@pytest.fixture
def mock_imagekit_sdk():
    """Mock the ImageKit SDK"""
    with patch("mcp_remote_exec.plugins.imagekit.imagekit_client.ImageKit") as mock:
        yield mock


class TestImageKitClientInitialization:
    """Tests for ImageKitClient initialization"""

    def test_client_initialization(self, imagekit_config, mock_imagekit_sdk):
        """Test that ImageKitClient initializes correctly"""
        client = ImageKitClient(imagekit_config)

        assert client is not None
        assert client.config == imagekit_config
        mock_imagekit_sdk.assert_called_once_with(
            private_key="test_private_key",
            public_key="test_public_key",
            url_endpoint="https://ik.imagekit.io/test",
        )


class TestGenerateUploadToken:
    """Tests for generate_upload_token method"""

    def test_generate_upload_token(self, imagekit_config, mock_imagekit_sdk):
        """Test generating upload token"""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_authentication_parameters.return_value = {
            "token": "test_token",
            "expire": 1234567890,
            "signature": "test_signature",
        }
        mock_imagekit_sdk.return_value = mock_sdk_instance

        client = ImageKitClient(imagekit_config)
        result = client.generate_upload_token("test_file.txt")

        assert result["token"] == "test_token"
        assert result["expire"] == 1234567890
        assert result["signature"] == "test_signature"
        assert result["file_name"] == "test_file.txt"
        assert result["public_key"] == "test_public_key"


class TestBuildUploadCommand:
    """Tests for build_upload_command method"""

    def test_build_upload_command(self, imagekit_config, mock_imagekit_sdk):
        """Test building upload command"""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_authentication_parameters.return_value = {
            "token": "test_token",
            "expire": 1234567890,
            "signature": "test_signature",
        }
        mock_imagekit_sdk.return_value = mock_sdk_instance

        client = ImageKitClient(imagekit_config)
        command = client.build_upload_command("test_file.txt")

        # Verify curl command contains essential parts
        assert "curl -X POST" in command
        assert "upload.imagekit.io" in command
        assert "test_file.txt" in command
        assert "test_token" in command
        assert "test_signature" in command
        assert "/test-folder" in command
        assert "test_public_key" in command

    def test_build_upload_command_contains_placeholder(
        self, imagekit_config, mock_imagekit_sdk
    ):
        """Test upload command contains file path placeholder"""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_authentication_parameters.return_value = {
            "token": "t",
            "expire": 1,
            "signature": "s",
        }
        mock_imagekit_sdk.return_value = mock_sdk_instance

        client = ImageKitClient(imagekit_config)
        command = client.build_upload_command("test.txt")

        # Should contain placeholder for user to replace
        assert "LOCAL_FILE_PATH" in command
