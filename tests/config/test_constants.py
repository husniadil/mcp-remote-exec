"""Tests for Service Constants"""


from mcp_remote_exec.config import constants


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

    def test_default_transfer_timeout_defined(self):
        """Test default transfer timeout constant is defined"""
        assert hasattr(constants, "DEFAULT_TRANSFER_TIMEOUT_SECONDS")
        assert isinstance(constants.DEFAULT_TRANSFER_TIMEOUT_SECONDS, int)
        assert constants.DEFAULT_TRANSFER_TIMEOUT_SECONDS > 0

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
        assert constants.MSG_PATH_TRAVERSAL_ERROR.strip()
