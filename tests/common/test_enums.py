"""Tests for Common Enums"""

from mcp_remote_exec.common.enums import ResponseFormat


class TestResponseFormat:
    """Tests for ResponseFormat enum"""

    def test_text_format(self):
        """Test TEXT format value"""
        assert ResponseFormat.TEXT == "text"
        assert ResponseFormat.TEXT.value == "text"

    def test_json_format(self):
        """Test JSON format value"""
        assert ResponseFormat.JSON == "json"
        assert ResponseFormat.JSON.value == "json"

    def test_enum_members(self):
        """Test enum has exactly two members"""
        assert len(ResponseFormat) == 2
        assert set(ResponseFormat) == {ResponseFormat.TEXT, ResponseFormat.JSON}

    def test_string_comparison(self):
        """Test enum can be compared with strings"""
        assert ResponseFormat.TEXT == "text"
        assert ResponseFormat.JSON == "json"
