"""Tests for Shared Validators"""

import pytest

from mcp_remote_exec.presentation.validators import validate_octal_permissions


class TestValidateOctalPermissions:
    """Tests for validate_octal_permissions function"""

    def test_valid_permissions(self):
        """Test valid octal permission values"""
        assert validate_octal_permissions(644) == 644
        assert validate_octal_permissions(755) == 755
        assert validate_octal_permissions(600) == 600
        assert validate_octal_permissions(700) == 700

    def test_none_permissions(self):
        """Test None returns None"""
        assert validate_octal_permissions(None) is None

    def test_invalid_octal_digit(self):
        """Test invalid octal digits raise ValueError"""
        with pytest.raises(ValueError, match="Invalid octal permission value"):
            validate_octal_permissions(888)

        with pytest.raises(ValueError, match="Invalid octal permission value"):
            validate_octal_permissions(999)

        with pytest.raises(ValueError, match="Invalid octal permission value"):
            validate_octal_permissions(789)

    def test_zero_permission(self):
        """Test zero permission is valid"""
        assert validate_octal_permissions(0) == 0

    def test_single_digit_permission(self):
        """Test single digit permissions"""
        assert validate_octal_permissions(7) == 7
        assert validate_octal_permissions(5) == 5
