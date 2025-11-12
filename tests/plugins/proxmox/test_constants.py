"""Tests for Proxmox Plugin Constants"""

import pytest
from mcp_remote_exec.plugins.proxmox import constants


class TestProxmoxConstants:
    """Tests for Proxmox plugin constants"""

    def test_temp_file_prefix_defined(self):
        """Test TEMP_FILE_PREFIX constant is defined"""
        assert hasattr(constants, "TEMP_FILE_PREFIX")
        assert isinstance(constants.TEMP_FILE_PREFIX, str)

    def test_temp_file_prefix_not_empty(self):
        """Test TEMP_FILE_PREFIX is not empty"""
        assert constants.TEMP_FILE_PREFIX.strip()

    def test_temp_file_prefix_contains_mcp_remote_exec(self):
        """Test TEMP_FILE_PREFIX contains project identifier"""
        assert "mcp-remote-exec" in constants.TEMP_FILE_PREFIX

    def test_msg_container_not_found_defined(self):
        """Test MSG_CONTAINER_NOT_FOUND constant is defined"""
        assert hasattr(constants, "MSG_CONTAINER_NOT_FOUND")
        assert isinstance(constants.MSG_CONTAINER_NOT_FOUND, str)

    def test_msg_container_not_found_not_empty(self):
        """Test MSG_CONTAINER_NOT_FOUND is not empty"""
        assert constants.MSG_CONTAINER_NOT_FOUND.strip()

    def test_msg_container_not_found_helpful(self):
        """Test MSG_CONTAINER_NOT_FOUND provides helpful guidance"""
        msg = constants.MSG_CONTAINER_NOT_FOUND
        # Should mention how to list containers
        assert "list" in msg.lower() or "containers" in msg.lower()

    def test_error_messages_not_empty(self):
        """Test all error message constants are not empty"""
        assert constants.MSG_CONTAINER_NOT_FOUND.strip()
