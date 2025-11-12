"""Tests for ImageKit Plugin Models"""

import pytest
from pydantic import ValidationError

from mcp_remote_exec.plugins.imagekit.models import (
    TransferOperation,
    ImageKitRequestUploadInput,
    ImageKitConfirmUploadInput,
    ImageKitRequestDownloadInput,
    ImageKitConfirmDownloadInput,
)


class TestTransferOperation:
    """Tests for TransferOperation enum"""

    def test_transfer_operation_upload(self):
        """Test UPLOAD operation value"""
        assert TransferOperation.UPLOAD.value == "upload"

    def test_transfer_operation_download(self):
        """Test DOWNLOAD operation value"""
        assert TransferOperation.DOWNLOAD.value == "download"


class TestImageKitRequestUploadInput:
    """Tests for ImageKitRequestUploadInput model"""

    def test_valid_upload_request(self):
        """Test valid upload request input"""
        input_data = ImageKitRequestUploadInput(
            remote_path="/remote/file.txt",
            permissions=644,
            overwrite=False,
            ctid=100,
        )
        assert input_data.remote_path == "/remote/file.txt"
        assert input_data.permissions == 644
        assert input_data.overwrite is False
        assert input_data.ctid == 100

    def test_optional_ctid(self):
        """Test optional container ID"""
        input_data = ImageKitRequestUploadInput(remote_path="/remote/file.txt")
        assert input_data.ctid is None

    def test_permissions_defaults_to_none(self):
        """Test permissions defaults to None"""
        input_data = ImageKitRequestUploadInput(remote_path="/remote/file.txt")
        assert input_data.permissions is None

    def test_path_length_validation(self):
        """Test remote path length validation"""
        # Valid path
        input_data = ImageKitRequestUploadInput(remote_path="/remote/file.txt")
        assert input_data.remote_path == "/remote/file.txt"

        # Path too long
        long_path = "a" * 4097
        with pytest.raises(ValidationError):
            ImageKitRequestUploadInput(remote_path=long_path)

        # Empty path
        with pytest.raises(ValidationError):
            ImageKitRequestUploadInput(remote_path="")


class TestImageKitConfirmUploadInput:
    """Tests for ImageKitConfirmUploadInput model"""

    def test_valid_confirm_upload(self):
        """Test valid upload confirmation"""
        input_data = ImageKitConfirmUploadInput(
            transfer_id="abc-123-def", file_id="file_123"
        )
        assert input_data.transfer_id == "abc-123-def"
        assert input_data.file_id == "file_123"

    def test_optional_file_id(self):
        """Test optional file_id parameter"""
        input_data = ImageKitConfirmUploadInput(transfer_id="abc-123-def")
        assert input_data.transfer_id == "abc-123-def"
        assert input_data.file_id is None


class TestImageKitRequestDownloadInput:
    """Tests for ImageKitRequestDownloadInput model"""

    def test_valid_download_request(self):
        """Test valid download request input"""
        input_data = ImageKitRequestDownloadInput(
            remote_path="/remote/file.txt", ctid=100
        )
        assert input_data.remote_path == "/remote/file.txt"
        assert input_data.ctid == 100

    def test_optional_ctid_download(self):
        """Test optional container ID for download"""
        input_data = ImageKitRequestDownloadInput(remote_path="/remote/file.txt")
        assert input_data.ctid is None

    def test_path_validation_download(self):
        """Test download path validation"""
        # Valid path
        input_data = ImageKitRequestDownloadInput(remote_path="/remote/file.txt")
        assert input_data.remote_path == "/remote/file.txt"

        # Path too long
        long_path = "a" * 4097
        with pytest.raises(ValidationError):
            ImageKitRequestDownloadInput(remote_path=long_path)


class TestImageKitConfirmDownloadInput:
    """Tests for ImageKitConfirmDownloadInput model"""

    def test_valid_confirm_download(self):
        """Test valid download confirmation"""
        input_data = ImageKitConfirmDownloadInput(transfer_id="abc-123-def")
        assert input_data.transfer_id == "abc-123-def"

    def test_empty_transfer_id(self):
        """Test empty transfer_id validation"""
        with pytest.raises(ValidationError):
            ImageKitConfirmDownloadInput(transfer_id="")
