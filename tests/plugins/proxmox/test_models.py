"""Tests for Proxmox Plugin Models"""

import pytest
from pydantic import ValidationError

from mcp_remote_exec.plugins.proxmox.models import (
    ProxmoxContainerExecInput,
    ProxmoxListContainersInput,
    ProxmoxContainerStatusInput,
    ProxmoxContainerActionInput,
    ProxmoxDownloadFileInput,
    ProxmoxUploadFileInput,
)
from mcp_remote_exec.presentation.models import ResponseFormat


class TestProxmoxContainerExecInput:
    """Tests for ProxmoxContainerExecInput model"""

    def test_valid_exec_input(self):
        """Test valid container exec input"""
        input_data = ProxmoxContainerExecInput(
            ctid=100,
            command="ls -la",
            timeout=30,
            response_format=ResponseFormat.TEXT,
        )
        assert input_data.ctid == 100
        assert input_data.command == "ls -la"
        assert input_data.timeout == 30

    def test_ctid_validation(self):
        """Test container ID validation"""
        # Valid ctid
        input_data = ProxmoxContainerExecInput(ctid=100, command="ls")
        assert input_data.ctid == 100

        # CTID too low
        with pytest.raises(ValidationError):
            ProxmoxContainerExecInput(ctid=99, command="ls")

        # CTID too high
        with pytest.raises(ValidationError):
            ProxmoxContainerExecInput(ctid=1000000000, command="ls")


class TestProxmoxUploadFileInput:
    """Tests for ProxmoxUploadFileInput model"""

    def test_valid_upload_input(self):
        """Test valid upload input"""
        input_data = ProxmoxUploadFileInput(
            ctid=100,
            local_path="/local/file.txt",
            container_path="/container/file.txt",
            permissions=644,
            overwrite=False,
        )
        assert input_data.ctid == 100
        assert input_data.local_path == "/local/file.txt"
        assert input_data.container_path == "/container/file.txt"
        assert input_data.permissions == 644

    def test_permissions_defaults_to_none(self):
        """Test permissions defaults to None for flexibility"""
        input_data = ProxmoxUploadFileInput(
            ctid=100,
            local_path="/local/file.txt",
            container_path="/container/file.txt",
        )
        assert input_data.permissions is None

    def test_path_length_validation(self):
        """Test path length validation"""
        # Valid paths
        input_data = ProxmoxUploadFileInput(
            ctid=100, local_path="/local/file.txt", container_path="/container/file.txt"
        )
        assert input_data.local_path == "/local/file.txt"

        # Path too long
        long_path = "a" * 4097
        with pytest.raises(ValidationError):
            ProxmoxUploadFileInput(
                ctid=100, local_path=long_path, container_path="/container/file.txt"
            )


class TestProxmoxDownloadFileInput:
    """Tests for ProxmoxDownloadFileInput model"""

    def test_valid_download_input(self):
        """Test valid download input"""
        input_data = ProxmoxDownloadFileInput(
            ctid=100,
            container_path="/container/file.txt",
            local_path="/local/file.txt",
            overwrite=True,
        )
        assert input_data.ctid == 100
        assert input_data.container_path == "/container/file.txt"
        assert input_data.local_path == "/local/file.txt"
        assert input_data.overwrite is True


class TestProxmoxContainerActionInput:
    """Tests for ProxmoxContainerActionInput model"""

    def test_valid_action_input(self):
        """Test valid container action input"""
        input_data = ProxmoxContainerActionInput(ctid=100)
        assert input_data.ctid == 100

    def test_ctid_boundary_validation(self):
        """Test ctid boundary values"""
        # Minimum valid ctid
        input_data = ProxmoxContainerActionInput(ctid=100)
        assert input_data.ctid == 100

        # High valid ctid
        input_data = ProxmoxContainerActionInput(ctid=999999999)
        assert input_data.ctid == 999999999
