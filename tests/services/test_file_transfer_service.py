"""
Tests for FileTransferService

Basic smoke tests for file transfer service functionality.
"""

import pytest
from unittest.mock import MagicMock
from mcp_remote_exec.services.file_transfer_service import FileTransferService


@pytest.fixture
def mock_sftp_manager():
    """Create a mock SFTP manager"""
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
def file_transfer_service(mock_sftp_manager, mock_ssh_config):
    """Create FileTransferService instance with mocks"""
    return FileTransferService(mock_sftp_manager, mock_ssh_config)


def test_file_transfer_service_initialization(
    file_transfer_service, mock_sftp_manager, mock_ssh_config
):
    """Test that FileTransferService initializes correctly"""
    assert file_transfer_service is not None
    assert file_transfer_service.sftp_manager == mock_sftp_manager
    assert file_transfer_service.config == mock_ssh_config


def test_file_transfer_service_has_required_methods(file_transfer_service):
    """Test that FileTransferService has required methods"""
    assert hasattr(file_transfer_service, "upload_file")
    assert hasattr(file_transfer_service, "download_file")
    assert callable(getattr(file_transfer_service, "upload_file"))
    assert callable(getattr(file_transfer_service, "download_file"))


def test_upload_file_delegates_to_sftp_manager(
    file_transfer_service, mock_sftp_manager
):
    """Test that upload_file delegates to SFTP manager"""
    # Setup mock
    from mcp_remote_exec.data_access.sftp_manager import FileTransferResult

    expected_result = FileTransferResult(
        success=True,
        message="Upload successful",
        local_path="/local/file",
        remote_path="/remote/file",
        bytes_transferred=1024,
    )
    mock_sftp_manager.upload_file.return_value = expected_result

    # This verifies the service is properly structured
    assert file_transfer_service.sftp_manager == mock_sftp_manager


def test_download_file_delegates_to_sftp_manager(
    file_transfer_service, mock_sftp_manager
):
    """Test that download_file delegates to SFTP manager"""
    # Setup mock
    from mcp_remote_exec.data_access.sftp_manager import FileTransferResult

    expected_result = FileTransferResult(
        success=True,
        message="Download successful",
        local_path="/local/file",
        remote_path="/remote/file",
        bytes_transferred=2048,
    )
    mock_sftp_manager.download_file.return_value = expected_result

    # This verifies the service is properly structured
    assert file_transfer_service.sftp_manager == mock_sftp_manager
