"""Tests for ImageKit Transfer Manager"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from mcp_remote_exec.plugins.imagekit.transfer_manager import TransferManager
from mcp_remote_exec.plugins.imagekit.models import TransferOperation, TransferState


@pytest.fixture
def transfer_manager():
    """Create a TransferManager instance for testing"""
    return TransferManager(timeout_seconds=3600)


class TestTransferManagerInitialization:
    """Tests for TransferManager initialization"""

    def test_initialization_with_default_timeout(self):
        """Test TransferManager initializes with default timeout"""
        manager = TransferManager()

        assert manager.timeout_seconds == 3600
        assert manager.get_active_count() == 0

    def test_initialization_with_custom_timeout(self):
        """Test TransferManager initializes with custom timeout"""
        manager = TransferManager(timeout_seconds=7200)

        assert manager.timeout_seconds == 7200
        assert manager.get_active_count() == 0


class TestCreateTransfer:
    """Tests for create_transfer method"""

    def test_create_upload_transfer(self, transfer_manager):
        """Test creating an upload transfer"""
        transfer = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
            permissions=644,
            overwrite=False,
        )

        assert isinstance(transfer, TransferState)
        assert transfer.transfer_id is not None
        assert transfer.operation == TransferOperation.UPLOAD
        assert transfer.remote_path == "/tmp/test.txt"
        assert transfer.permissions == 644
        assert transfer.overwrite is False
        assert transfer.ctid is None
        assert isinstance(transfer.timestamp, datetime)

    def test_create_download_transfer(self, transfer_manager):
        """Test creating a download transfer"""
        transfer = transfer_manager.create_transfer(
            operation=TransferOperation.DOWNLOAD,
            remote_path="/var/log/app.log",
        )

        assert transfer.operation == TransferOperation.DOWNLOAD
        assert transfer.remote_path == "/var/log/app.log"
        assert transfer.permissions is None
        assert transfer.overwrite is False

    def test_create_transfer_with_container(self, transfer_manager):
        """Test creating a transfer with container ID"""
        transfer = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/app/config.txt",
            ctid=100,
        )

        assert transfer.ctid == 100
        assert transfer.remote_path == "/app/config.txt"

    def test_create_transfer_generates_unique_ids(self, transfer_manager):
        """Test that each transfer gets a unique ID"""
        transfer1 = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/file1.txt",
        )
        transfer2 = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/file2.txt",
        )

        assert transfer1.transfer_id != transfer2.transfer_id

    def test_create_transfer_increments_active_count(self, transfer_manager):
        """Test that creating transfers increments active count"""
        assert transfer_manager.get_active_count() == 0

        transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
        )
        assert transfer_manager.get_active_count() == 1

        transfer_manager.create_transfer(
            operation=TransferOperation.DOWNLOAD,
            remote_path="/tmp/test2.txt",
        )
        assert transfer_manager.get_active_count() == 2


class TestGetTransfer:
    """Tests for get_transfer method"""

    def test_get_existing_transfer(self, transfer_manager):
        """Test retrieving an existing transfer"""
        created = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
        )

        retrieved = transfer_manager.get_transfer(created.transfer_id)

        assert retrieved is not None
        assert retrieved.transfer_id == created.transfer_id
        assert retrieved.remote_path == created.remote_path

    def test_get_nonexistent_transfer(self, transfer_manager):
        """Test retrieving a non-existent transfer returns None"""
        result = transfer_manager.get_transfer("nonexistent-id")

        assert result is None


class TestUpdateTransfer:
    """Tests for update_transfer method"""

    def test_update_transfer_with_file_id(self, transfer_manager):
        """Test updating transfer with ImageKit file ID"""
        transfer = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
        )

        success = transfer_manager.update_transfer(
            transfer.transfer_id,
            imagekit_file_id="ik_file_123",
        )

        assert success is True
        updated = transfer_manager.get_transfer(transfer.transfer_id)
        assert updated.imagekit_file_id == "ik_file_123"

    def test_update_nonexistent_transfer(self, transfer_manager):
        """Test updating non-existent transfer returns False"""
        success = transfer_manager.update_transfer(
            "nonexistent-id",
            imagekit_file_id="ik_file_123",
        )

        assert success is False


class TestCompleteTransfer:
    """Tests for complete_transfer method"""

    def test_complete_existing_transfer(self, transfer_manager):
        """Test completing an existing transfer"""
        transfer = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
        )
        transfer_id = transfer.transfer_id

        assert transfer_manager.get_active_count() == 1

        completed = transfer_manager.complete_transfer(transfer_id)

        assert completed is not None
        assert completed.transfer_id == transfer_id
        assert transfer_manager.get_active_count() == 0
        assert transfer_manager.get_transfer(transfer_id) is None

    def test_complete_nonexistent_transfer(self, transfer_manager):
        """Test completing non-existent transfer returns None"""
        result = transfer_manager.complete_transfer("nonexistent-id")

        assert result is None


class TestCleanupExpiredTransfers:
    """Tests for cleanup_expired_transfers method"""

    def test_cleanup_expired_transfers(self, transfer_manager):
        """Test cleaning up expired transfers"""
        # Create a transfer with old timestamp
        old_time = datetime.now() - timedelta(seconds=7200)  # 2 hours ago

        with patch("mcp_remote_exec.plugins.imagekit.transfer_manager.datetime") as mock_dt:
            mock_dt.now.return_value = old_time
            old_transfer = transfer_manager.create_transfer(
                operation=TransferOperation.UPLOAD,
                remote_path="/tmp/old.txt",
            )

        # Create a fresh transfer
        fresh_transfer = transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/fresh.txt",
        )

        assert transfer_manager.get_active_count() == 2

        # Cleanup expired (older than 1 hour)
        removed_count = transfer_manager.cleanup_expired_transfers()

        assert removed_count == 1
        assert transfer_manager.get_active_count() == 1
        assert transfer_manager.get_transfer(old_transfer.transfer_id) is None
        assert transfer_manager.get_transfer(fresh_transfer.transfer_id) is not None

    def test_cleanup_no_expired_transfers(self, transfer_manager):
        """Test cleanup when no transfers are expired"""
        transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/test.txt",
        )

        removed_count = transfer_manager.cleanup_expired_transfers()

        assert removed_count == 0
        assert transfer_manager.get_active_count() == 1

    def test_cleanup_all_expired(self, transfer_manager):
        """Test cleanup when all transfers are expired"""
        old_time = datetime.now() - timedelta(seconds=7200)

        with patch("mcp_remote_exec.plugins.imagekit.transfer_manager.datetime") as mock_dt:
            mock_dt.now.return_value = old_time
            transfer_manager.create_transfer(
                operation=TransferOperation.UPLOAD,
                remote_path="/tmp/file1.txt",
            )
            transfer_manager.create_transfer(
                operation=TransferOperation.DOWNLOAD,
                remote_path="/tmp/file2.txt",
            )

        assert transfer_manager.get_active_count() == 2

        removed_count = transfer_manager.cleanup_expired_transfers()

        assert removed_count == 2
        assert transfer_manager.get_active_count() == 0


class TestClearAll:
    """Tests for clear_all method"""

    def test_clear_all_transfers(self, transfer_manager):
        """Test clearing all transfers"""
        transfer_manager.create_transfer(
            operation=TransferOperation.UPLOAD,
            remote_path="/tmp/file1.txt",
        )
        transfer_manager.create_transfer(
            operation=TransferOperation.DOWNLOAD,
            remote_path="/tmp/file2.txt",
        )

        assert transfer_manager.get_active_count() == 2

        transfer_manager.clear_all()

        assert transfer_manager.get_active_count() == 0

    def test_clear_all_when_empty(self, transfer_manager):
        """Test clearing when no transfers exist"""
        assert transfer_manager.get_active_count() == 0

        transfer_manager.clear_all()

        assert transfer_manager.get_active_count() == 0
