"""Tests for ImageKit Plugin Constants"""

from mcp_remote_exec.plugins.imagekit import constants


class TestImageKitConstants:
    """Tests for ImageKit plugin constants"""

    def test_msg_proxmox_required_defined(self):
        """Test MSG_PROXMOX_REQUIRED constant is defined"""
        assert hasattr(constants, "MSG_PROXMOX_REQUIRED")
        assert isinstance(constants.MSG_PROXMOX_REQUIRED, str)

    def test_msg_proxmox_required_not_empty(self):
        """Test MSG_PROXMOX_REQUIRED is not empty"""
        assert constants.MSG_PROXMOX_REQUIRED.strip()

    def test_msg_proxmox_required_mentions_plugin(self):
        """Test MSG_PROXMOX_REQUIRED mentions Proxmox plugin"""
        msg = constants.MSG_PROXMOX_REQUIRED
        assert "proxmox" in msg.lower() or "container" in msg.lower()

    def test_msg_proxmox_enable_suggestion_defined(self):
        """Test MSG_PROXMOX_ENABLE_SUGGESTION constant is defined"""
        assert hasattr(constants, "MSG_PROXMOX_ENABLE_SUGGESTION")
        assert isinstance(constants.MSG_PROXMOX_ENABLE_SUGGESTION, str)

    def test_msg_proxmox_enable_suggestion_not_empty(self):
        """Test MSG_PROXMOX_ENABLE_SUGGESTION is not empty"""
        assert constants.MSG_PROXMOX_ENABLE_SUGGESTION.strip()

    def test_msg_proxmox_enable_suggestion_helpful(self):
        """Test MSG_PROXMOX_ENABLE_SUGGESTION provides actionable guidance"""
        msg = constants.MSG_PROXMOX_ENABLE_SUGGESTION
        # Should mention the environment variable
        assert "ENABLE_PROXMOX" in msg

    def test_msg_transfer_not_found_defined(self):
        """Test MSG_TRANSFER_NOT_FOUND constant is defined"""
        assert hasattr(constants, "MSG_TRANSFER_NOT_FOUND")
        assert isinstance(constants.MSG_TRANSFER_NOT_FOUND, str)

    def test_msg_transfer_not_found_not_empty(self):
        """Test MSG_TRANSFER_NOT_FOUND is not empty"""
        assert constants.MSG_TRANSFER_NOT_FOUND.strip()

    def test_msg_transfer_not_found_mentions_transfer(self):
        """Test MSG_TRANSFER_NOT_FOUND mentions transfer"""
        msg = constants.MSG_TRANSFER_NOT_FOUND
        assert "transfer" in msg.lower() or "expired" in msg.lower()

    def test_msg_config_not_found_defined(self):
        """Test MSG_CONFIG_NOT_FOUND constant is defined"""
        assert hasattr(constants, "MSG_CONFIG_NOT_FOUND")
        assert isinstance(constants.MSG_CONFIG_NOT_FOUND, str)

    def test_msg_config_not_found_not_empty(self):
        """Test MSG_CONFIG_NOT_FOUND is not empty"""
        assert constants.MSG_CONFIG_NOT_FOUND.strip()

    def test_msg_config_not_found_mentions_config(self):
        """Test MSG_CONFIG_NOT_FOUND mentions ImageKit config"""
        msg = constants.MSG_CONFIG_NOT_FOUND
        assert "imagekit" in msg.lower() or "config" in msg.lower()

    def test_all_error_messages_not_empty(self):
        """Test all error message constants are not empty"""
        assert constants.MSG_PROXMOX_REQUIRED.strip()
        assert constants.MSG_PROXMOX_ENABLE_SUGGESTION.strip()
        assert constants.MSG_TRANSFER_NOT_FOUND.strip()
        assert constants.MSG_CONFIG_NOT_FOUND.strip()

    def test_all_constants_are_strings(self):
        """Test all constants are strings"""
        assert isinstance(constants.MSG_PROXMOX_REQUIRED, str)
        assert isinstance(constants.MSG_PROXMOX_ENABLE_SUGGESTION, str)
        assert isinstance(constants.MSG_TRANSFER_NOT_FOUND, str)
        assert isinstance(constants.MSG_CONFIG_NOT_FOUND, str)
