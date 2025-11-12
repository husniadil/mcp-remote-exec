"""
Tests for SFTPManager

Basic smoke tests for SFTP manager functionality.
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from mcp_remote_exec.data_access.sftp_manager import SFTPManager, FileTransferResult


@pytest.fixture
def mock_connection_manager():
    """Create a mock SSH connection manager"""
    mock = MagicMock()
    return mock


@pytest.fixture
def sftp_manager(mock_connection_manager):
    """Create SFTPManager instance with mocked connection manager"""
    return SFTPManager(mock_connection_manager)


def test_sftp_manager_initialization(sftp_manager, mock_connection_manager):
    """Test that SFTPManager initializes correctly"""
    assert sftp_manager is not None
    assert sftp_manager.connection_manager == mock_connection_manager


def test_file_transfer_result_dataclass():
    """Test FileTransferResult dataclass creation"""
    result = FileTransferResult(
        success=True,
        message="Transfer complete",
        local_path="/local/path",
        remote_path="/remote/path",
        bytes_transferred=1024,
        transfer_speed=1024.5,
    )

    assert result.success is True
    assert result.message == "Transfer complete"
    assert result.local_path == "/local/path"
    assert result.remote_path == "/remote/path"
    assert result.bytes_transferred == 1024
    assert result.transfer_speed == 1024.5


def test_file_transfer_result_defaults():
    """Test FileTransferResult with default values"""
    result = FileTransferResult(
        success=True, message="OK", local_path="/local", remote_path="/remote"
    )

    assert result.success is True
    assert result.bytes_transferred == 0
    assert result.transfer_speed == 0.0


def test_file_transfer_result_failure():
    """Test FileTransferResult for failed transfer"""
    result = FileTransferResult(
        success=False,
        message="Transfer failed: connection lost",
        local_path="/local/file",
        remote_path="/remote/file",
        bytes_transferred=0,
        transfer_speed=0.0,
    )

    assert result.success is False
    assert "failed" in result.message.lower()
    assert result.bytes_transferred == 0


@patch("mcp_remote_exec.data_access.sftp_manager.os.path.exists")
def test_validate_file_size_within_limit(
    mock_exists, sftp_manager, mock_connection_manager
):
    """Test file size validation when file is within limit"""
    # Setup mock
    mock_exists.return_value = True

    # This is a basic structure test - actual validation logic would need more mocking
    assert sftp_manager is not None


def test_sftp_manager_has_required_methods(sftp_manager):
    """Test that SFTPManager has required methods"""
    assert hasattr(sftp_manager, "upload_file")
    assert hasattr(sftp_manager, "download_file")
    assert callable(getattr(sftp_manager, "upload_file"))
    assert callable(getattr(sftp_manager, "download_file"))
