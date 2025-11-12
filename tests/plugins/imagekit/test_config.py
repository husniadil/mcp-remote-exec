"""Tests for ImageKit Plugin Configuration"""

import os
import pytest
from unittest.mock import patch

from mcp_remote_exec.plugins.imagekit.config import ImageKitConfig
from mcp_remote_exec.config.constants import DEFAULT_TRANSFER_TIMEOUT_SECONDS


class TestImageKitConfigFromEnv:
    """Tests for ImageKitConfig.from_env() method"""

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_test_key",
            "IMAGEKIT_PRIVATE_KEY": "private_test_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_enabled_with_credentials(self):
        """Test from_env() returns config when enabled with valid credentials"""
        config = ImageKitConfig.from_env()

        assert config is not None
        assert isinstance(config, ImageKitConfig)
        assert config.public_key == "public_test_key"
        assert config.private_key == "private_test_key"
        assert config.url_endpoint == "https://ik.imagekit.io/test"
        assert config.folder == "/mcp-remote-exec"  # Default value
        assert config.transfer_timeout == DEFAULT_TRANSFER_TIMEOUT_SECONDS

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
            "IMAGEKIT_FOLDER": "/custom-folder",
            "IMAGEKIT_TRANSFER_TIMEOUT": "7200",
        },
    )
    def test_from_env_with_custom_settings(self):
        """Test from_env() respects custom folder and timeout"""
        config = ImageKitConfig.from_env()

        assert config is not None
        assert config.folder == "/custom-folder"
        assert config.transfer_timeout == 7200

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "false",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_disabled_with_credentials(self):
        """Test from_env() returns None when ENABLE_IMAGEKIT=false even with credentials"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(os.environ, {}, clear=True)
    def test_from_env_not_enabled_missing_var(self):
        """Test from_env() returns None when ENABLE_IMAGEKIT is not set"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            # Missing IMAGEKIT_PUBLIC_KEY
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_missing_public_key(self):
        """Test from_env() returns None when public key is missing"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            # Missing IMAGEKIT_PRIVATE_KEY
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_missing_private_key(self):
        """Test from_env() returns None when private key is missing"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            # Missing IMAGEKIT_URL_ENDPOINT
        },
    )
    def test_from_env_missing_url_endpoint(self):
        """Test from_env() returns None when URL endpoint is missing"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "",  # Empty string
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_empty_public_key(self):
        """Test from_env() returns None when public key is empty string"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "",  # Empty string
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_empty_private_key(self):
        """Test from_env() returns None when private key is empty string"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "true",
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "",  # Empty string
        },
    )
    def test_from_env_empty_url_endpoint(self):
        """Test from_env() returns None when URL endpoint is empty string"""
        config = ImageKitConfig.from_env()

        assert config is None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "TRUE",  # Uppercase
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_case_insensitive_enable(self):
        """Test from_env() handles case-insensitive ENABLE_IMAGEKIT"""
        config = ImageKitConfig.from_env()

        assert config is not None

    @patch.dict(
        os.environ,
        {
            "ENABLE_IMAGEKIT": "yes",  # Invalid value
            "IMAGEKIT_PUBLIC_KEY": "public_key",
            "IMAGEKIT_PRIVATE_KEY": "private_key",
            "IMAGEKIT_URL_ENDPOINT": "https://ik.imagekit.io/test",
        },
    )
    def test_from_env_invalid_enable_value(self):
        """Test from_env() returns None for invalid ENABLE_IMAGEKIT values"""
        config = ImageKitConfig.from_env()

        assert config is None


class TestImageKitConfigDataclass:
    """Tests for ImageKitConfig dataclass"""

    def test_config_with_required_fields(self):
        """Test ImageKitConfig with required fields"""
        config = ImageKitConfig(
            public_key="test_public",
            private_key="test_private",
            url_endpoint="https://ik.imagekit.io/test",
        )

        assert config.public_key == "test_public"
        assert config.private_key == "test_private"
        assert config.url_endpoint == "https://ik.imagekit.io/test"
        assert config.folder == "/mcp-remote-exec"
        assert config.transfer_timeout == DEFAULT_TRANSFER_TIMEOUT_SECONDS

    def test_config_with_custom_folder(self):
        """Test ImageKitConfig with custom folder"""
        config = ImageKitConfig(
            public_key="key1",
            private_key="key2",
            url_endpoint="https://example.com",
            folder="/custom",
        )

        assert config.folder == "/custom"

    def test_config_with_custom_timeout(self):
        """Test ImageKitConfig with custom transfer timeout"""
        config = ImageKitConfig(
            public_key="key1",
            private_key="key2",
            url_endpoint="https://example.com",
            transfer_timeout=7200,
        )

        assert config.transfer_timeout == 7200

    def test_config_fields_are_mutable(self):
        """Test ImageKitConfig fields can be modified"""
        config = ImageKitConfig(
            public_key="key1",
            private_key="key2",
            url_endpoint="https://example.com",
        )

        config.folder = "/new-folder"
        assert config.folder == "/new-folder"
