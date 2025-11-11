"""Tests for Service Constants"""

import pytest

from mcp_remote_exec import constants


class TestConstants:
    """Tests for service layer constants"""

    def test_json_metadata_overhead_defined(self):
        """Test JSON metadata overhead constant is defined"""
        assert hasattr(constants, "JSON_METADATA_OVERHEAD")
        assert isinstance(constants.JSON_METADATA_OVERHEAD, int)
        assert constants.JSON_METADATA_OVERHEAD > 0

    def test_min_output_space_defined(self):
        """Test minimum output space constant is defined"""
        assert hasattr(constants, "MIN_OUTPUT_SPACE")
        assert isinstance(constants.MIN_OUTPUT_SPACE, int)
        assert constants.MIN_OUTPUT_SPACE > 0

    def test_temp_file_prefix_defined(self):
        """Test temp file prefix constant is defined"""
        import tempfile
        assert hasattr(constants, "TEMP_FILE_PREFIX")
        assert isinstance(constants.TEMP_FILE_PREFIX, str)
        # Should use system temp directory (varies by OS)
        assert constants.TEMP_FILE_PREFIX.startswith(tempfile.gettempdir())

    def test_default_transfer_timeout_defined(self):
        """Test default transfer timeout constant is defined"""
        assert hasattr(constants, "DEFAULT_TRANSFER_TIMEOUT_SECONDS")
        assert isinstance(constants.DEFAULT_TRANSFER_TIMEOUT_SECONDS, int)
        assert constants.DEFAULT_TRANSFER_TIMEOUT_SECONDS > 0

    def test_msg_container_not_found_defined(self):
        """Test container not found message constant is defined"""
        assert hasattr(constants, "MSG_CONTAINER_NOT_FOUND")
        assert isinstance(constants.MSG_CONTAINER_NOT_FOUND, str)
        assert len(constants.MSG_CONTAINER_NOT_FOUND) > 0

    def test_msg_path_traversal_error_exists(self):
        """Test path traversal error message constant exists"""
        assert hasattr(constants, "MSG_PATH_TRAVERSAL_ERROR")
        assert isinstance(constants.MSG_PATH_TRAVERSAL_ERROR, str)
        assert "traversal" in constants.MSG_PATH_TRAVERSAL_ERROR.lower()

    def test_constant_values_reasonable(self):
        """Test constants have reasonable values"""
        # JSON overhead should be reasonable (not too large)
        assert 100 < constants.JSON_METADATA_OVERHEAD < 10000

        # Min output space should be at least 100 chars
        assert constants.MIN_OUTPUT_SPACE >= 100

        # Transfer timeout should be reasonable (not too short or too long)
        assert 60 <= constants.DEFAULT_TRANSFER_TIMEOUT_SECONDS <= 86400

    def test_error_messages_not_empty(self):
        """Test error message constants are not empty"""
        assert constants.MSG_CONTAINER_NOT_FOUND.strip()
        assert constants.MSG_PATH_TRAVERSAL_ERROR.strip()

    def test_temp_file_prefix_format(self):
        """Test temp file prefix follows expected format"""
        import tempfile
        import os
        prefix = constants.TEMP_FILE_PREFIX
        # Should start with system temp directory
        assert prefix.startswith(tempfile.gettempdir())
        # Should contain project identifier
        assert "mcp-remote-exec" in prefix
        # Should be valid directory path format
        assert os.path.isabs(prefix)
